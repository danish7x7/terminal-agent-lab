"""Task-validation gate (decision 003, Option B): A -> B -> B' -> L -> C.

Our stand-in for the RL soft-filter the paper gets for free: without a gradient
to drop all-zero tasks, broken/unsolvable tasks must be caught explicitly or
they deflate pass@k. On Gate B' failure we run a bounded execution-feedback
repair loop (NOT model self-check — the failures prove the model can't catch
these by reading its own code; the repair signal comes from real verifier
output). Every task gets a durable gate.json; nothing is ever silently deleted.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import yaml

from harness.config import RunConfig
from harness.runner import run_task
from harness.sandbox import Sandbox, SandboxError, build_image
from harness.verifier import run_verifier
from pipeline.generator import GeneratorError, materialize_task, parse_generation
from pipeline.generator_prompt import SYSTEM_PROMPT
from pipeline.sampler import Signature

PASS_REWARD = 1.0  # both kinds pass iff all tests green (threshold lives in the test)
_BASH_RE = re.compile(r"```bash\n(.*?)```", re.DOTALL)
_STR_LITERAL_RE = re.compile(r"""(['"])(.+?)\1""")
_MIN_NEEDLE = 8  # shorter answers aren't distinctive enough to leak-check (003 limitation)

_META_FILES = {"task.md", "Dockerfile", "solution.md", "signature.yaml", "gate.json"}


@dataclass
class GateResult:
    task_id: str
    verdict: str = "quarantined"           # admitted | quarantined | unsolved
    reason: str | None = None              # build_failed|pre_solved|broken_test|answer_leak|unsolved_by_agent
    gate_A: bool | None = None
    gate_B_reward: float | None = None
    gate_B_prime_reward: float | None = None
    repair_attempts: int = 0
    gate_L_leak: bool | None = None
    gate_L_needle: str | None = None
    gate_C_successes: int | None = None
    gate_C_k: int | None = None
    verifier_output: str | None = None
    solution_steps: list | None = None
    build_error: str | None = None
    destination: str | None = None


def bucket_subdir(verdict: str) -> str:
    return {"admitted": "", "unsolved": "_unsolved", "quarantined": "_quarantine"}[verdict]


def read_generation(task_dir: Path) -> dict:
    """Reconstruct the generation dict from a materialized task dir."""
    tests = {p.name: p.read_text() for p in sorted((task_dir / "tests").iterdir()) if p.is_file()}
    fixtures = {}
    for p in sorted(task_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(task_dir)
        if "tests" in rel.parts or p.name in _META_FILES:
            continue
        fixtures[rel.as_posix()] = p.read_text()
    return {
        "task_md": (task_dir / "task.md").read_text(),
        "dockerfile": (task_dir / "Dockerfile").read_text(),
        "tests": tests,
        "solution_md": (task_dir / "solution.md").read_text(),
        "fixture_files": fixtures,
    }


def build_repair_prompt(generation: dict, verifier_output: str | None) -> str:
    return (
        "The task you generated FAILED its own reference solution: running "
        "solution_md on a fresh container did NOT make the tests pass. That is a "
        "hard defect — the reference must satisfy the task's own threshold/spec.\n\n"
        "The task you produced (same JSON schema):\n\n"
        + json.dumps(generation, separators=(",", ":"))
        + "\n\nVerifier output after running your reference solution:\n\n"
        + (verifier_output or "(none)")
        + "\n\nFix it, using this ACTUAL execution feedback (not your own reading "
        "of the code). Either correct solution_md so it genuinely passes, or, if "
        "the tests demand more than a sound approach can reach, lower the threshold "
        "in the test to what a correct approach actually achieves — but the fresh "
        "container (no solution) must STILL fail. Keep the answer key only in "
        "tests/ and task_md silent on grading. Output the full corrected JSON "
        "object only."
    )


def _apply_solution(sb: Sandbox, solution_md: str) -> list[dict]:
    steps = []
    for block in _BASH_RE.findall(solution_md):
        r = sb.exec(block, timeout=120)
        steps.append({"exit": r.returncode, "stdout": r.stdout[-1500:], "stderr": r.stderr[-1500:]})
    return steps


def _probe(task_dir: Path, cfg: RunConfig, tag: str):
    """Gate A + B + B': build, verify fresh, apply reference, verify again.

    Returns (build_ok, fresh_reward, solved_reward, verifier_output, build_error,
    solution_steps). Leaves the built image `tag` in place for Gate L; caller
    removes it.
    """
    try:
        build_image(task_dir, tag)
    except SandboxError as exc:
        return False, None, None, None, str(exc).splitlines()[-1], None
    with Sandbox(tag, cfg.container()) as sb:
        fresh = run_verifier(sb, str(task_dir / "tests"))
        steps = _apply_solution(sb, (task_dir / "solution.md").read_text())
        solved = run_verifier(sb, str(task_dir / "tests"))
    return True, fresh.reward, solved.reward, solved.output, None, steps


def _reset_task_dir(task_dir: Path) -> None:
    for p in list(task_dir.iterdir()):
        if p.name == "signature.yaml":
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()


def _rmi(tag: str) -> None:
    subprocess.run(["docker", "rmi", "-f", tag], capture_output=True)


def _is_answer_like(s: str) -> bool:
    """Keep only strings that could plausibly be a leaked answer. Exclude:
    - short/common strings (< _MIN_NEEDLE chars, e.g. 'high');
    - path-like strings (contain '/') — I/O paths such as '/output/totals.txt'
      legitimately appear in task.md, so matching them there is a false leak.
    Documented Gate L limitation (decision 003): verbatim, distinctive,
    non-path answers only."""
    return len(s) >= _MIN_NEEDLE and "/" not in s


def _distinctive_needles(task_dir: Path) -> list[str]:
    """Answer-bearing strings distinctive enough to leak-check: reference-file
    lines and test string literals that pass _is_answer_like."""
    needles: set[str] = set()
    for p in (task_dir / "tests").iterdir():
        if not p.is_file():
            continue
        text = p.read_text()
        if p.suffix == ".py":
            needles.update(m[1] for m in _STR_LITERAL_RE.findall(text))
        else:
            needles.update(line.strip() for line in text.splitlines())
    return [n for n in sorted(needles) if _is_answer_like(n)][:25]


def _leak_check(task_dir: Path, tag: str, cfg: RunConfig) -> tuple[bool, str | None]:
    """Gate L: is any distinctive answer reachable from task.md or the image?
    Runs on a fresh container (the agent's view — tests/ are not present)."""
    needles = _distinctive_needles(task_dir)
    if not needles:
        return False, None
    task_md = (task_dir / "task.md").read_text()
    for n in needles:
        if n in task_md:
            return True, n
    with Sandbox(tag, cfg.container()) as sb:
        for n in needles:
            q = n.replace("'", "'\\''")
            cmd = (
                "for d in /data /app /srv /root /home /opt /tmp /work; do "
                f"[ -e \"$d\" ] && grep -rIlF -- '{q}' \"$d\" 2>/dev/null; done; true"
            )
            if sb.exec(cmd, timeout=30).stdout.strip():
                return True, n
    return False, None


def _finalize(res: GateResult, verdict: str, reason: str | None, task_dir: Path, tasks_root: Path) -> GateResult:
    res.verdict, res.reason = verdict, reason
    subdir = bucket_subdir(verdict)
    dest_parent = tasks_root / subdir if subdir else tasks_root
    dest_parent.mkdir(parents=True, exist_ok=True)
    dest = dest_parent / task_dir.name
    res.destination = str(dest)
    (task_dir / "gate.json").write_text(json.dumps(asdict(res), indent=2))
    if dest.exists():
        shutil.rmtree(dest)
    shutil.move(str(task_dir), str(dest))
    return res


def run_gate(
    task_dir: str | Path,
    *,
    cfg: RunConfig | None = None,
    repair_client=None,
    max_repairs: int = 2,
    gate_c_model: str = "claude-sonnet-4-6",
    gate_c_k: int = 4,
    tasks_root: str | Path = "tasks",
    eval_out: str | Path = "evals/results",
) -> GateResult:
    """Run one candidate task dir through A -> B -> B' -> L -> C, moving it to its
    bucket and writing a durable gate.json. `repair_client` (any .chat client)
    enables the Gate B' repair loop; omit it for Option-A behaviour."""
    task_dir = Path(task_dir)
    tasks_root = Path(tasks_root)
    cfg = cfg or RunConfig()
    sig = Signature(**yaml.safe_load((task_dir / "signature.yaml").read_text()))
    res = GateResult(task_id=task_dir.name, gate_C_k=gate_c_k)

    tag = f"tal-gate-{task_dir.name}"
    build_ok, fresh, solved, vout, berr, steps = _probe(task_dir, cfg, tag)
    res.gate_A, res.gate_B_reward, res.gate_B_prime_reward = build_ok, fresh, solved
    res.verifier_output, res.build_error, res.solution_steps = vout, berr, steps
    if not build_ok:
        return _finalize(res, "quarantined", "build_failed", task_dir, tasks_root)
    if fresh >= PASS_REWARD:
        _rmi(tag)
        return _finalize(res, "quarantined", "pre_solved", task_dir, tasks_root)

    # Gate B' repair loop (Option B): feed real verifier output back to the model.
    while solved < PASS_REWARD and res.repair_attempts < max_repairs and repair_client is not None:
        res.repair_attempts += 1
        _rmi(tag)
        try:
            prompt = build_repair_prompt(read_generation(task_dir), vout)
            reply = repair_client.chat(SYSTEM_PROMPT, [{"role": "user", "content": prompt}])
            data = parse_generation(reply.text)
        except GeneratorError:
            break  # repair produced unparseable output; give up
        _reset_task_dir(task_dir)
        materialize_task(data, task_dir, sig)
        tag = f"tal-gate-{task_dir.name}-r{res.repair_attempts}"
        build_ok, fresh, solved, vout, berr, steps = _probe(task_dir, cfg, tag)
        res.gate_A, res.gate_B_reward, res.gate_B_prime_reward = build_ok, fresh, solved
        res.verifier_output, res.build_error, res.solution_steps = vout, berr, steps
        if not build_ok:
            return _finalize(res, "quarantined", "broken_test", task_dir, tasks_root)
        if fresh >= PASS_REWARD:
            _rmi(tag)
            return _finalize(res, "quarantined", "pre_solved", task_dir, tasks_root)

    if solved < PASS_REWARD:
        _rmi(tag)
        return _finalize(res, "quarantined", "broken_test", task_dir, tasks_root)

    # Gate L: answer-leak.
    leak, needle = _leak_check(task_dir, tag, cfg)
    res.gate_L_leak, res.gate_L_needle = leak, needle
    _rmi(tag)
    if leak:
        return _finalize(res, "quarantined", "answer_leak", task_dir, tasks_root)

    # Gate C: solvable-by-agent, full k, no early-stop (reuses runner + parity cfg).
    ccfg = replace(cfg, model=gate_c_model, k=gate_c_k)
    summary = run_task(task_dir, ccfg, out_dir=eval_out)
    res.gate_C_successes = summary["successes"]
    if summary["successes"] == 0:
        return _finalize(res, "unsolved", "unsolved_by_agent", task_dir, tasks_root)
    return _finalize(res, "admitted", None, task_dir, tasks_root)
