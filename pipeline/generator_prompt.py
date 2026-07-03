"""Build the generator system + user prompts from a task signature.

Design: decision 003 §3. One API call per signature, single-JSON output. The
hard requirements each map to a gate or harness rule so a well-behaved
generation passes A/B/B'/L/C by construction.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.base_images import base_image_for
from pipeline.sampler import Signature

EXEMPLARS_DIR = Path(__file__).parent / "exemplars"

OUTPUT_KEYS = (
    "- task_md (string): the instructions shown to the agent.\n"
    "- dockerfile (string): a Dockerfile starting FROM the given base image.\n"
    "- tests (object): filename -> file contents; the pytest verifier plus any\n"
    "  reference/answer files it reads.\n"
    "- solution_md (string): a RUNNABLE reference solution (a ```bash block).\n"
    "- fixture_files (object): path -> file contents; build-context input files\n"
    "  the Dockerfile COPYs into the image."
)

SYSTEM_PROMPT = f"""You author self-contained evaluation tasks for a terminal agent.

The agent that will solve your task is a TEXT-ONLY model driving one bash
command per turn in a persistent shell inside a Docker container: no network at
runtime, ~30 steps, 120 s per command. It never sees your tests or solution.

Produce ONE task. Output a SINGLE, STRICT JSON object and nothing else — no
prose, no markdown fence, no comments, all keys and strings double-quoted, no
trailing commas. Your reply must BEGIN with {{ and END with }}: do NOT write
any reasoning, planning, or verification before or after the object — not one
word, do not think out loud, emit only the JSON. (Reasoning before the JSON
wastes the token budget and truncates the object.) It must have exactly these
keys:

{OUTPUT_KEYS}

HARD REQUIREMENTS (a violation makes the task unusable):
1. Dockerfile must start `FROM <base image given below>` and install deps only
   via apt-get/pip. ALL downloads happen at build time — runtime has no network.
   Keep the Dockerfile valid: each `RUN` is a single shell command. To generate
   files at build time use a heredoc (`RUN cat > /path <<'EOF' ... EOF`) or ship
   the file via `fixture_files` and `COPY` it — never inline a raw multi-line
   `python3 -c "..."` with newlines in the string (Docker cannot parse it).
2. `tests/` must FAIL on the freshly-built container (before any solution) and
   PASS after a correct solution. Tests use pytest, check OUTCOMES not the
   procedure, and must not depend on the agent's shell state.
3. The reference answer / expected output the tests compare against lives ONLY
   inside `tests/` (e.g. an `answers.txt` the test reads). It must NOT appear in
   the image (no COPY of it, not derivable from shipped files) and must NOT
   appear in `task_md`. Putting the answer where the agent can read it is an
   automatic rejection.
4. `task_md` states the goal and the required output location/format. It must
   NEVER mention tests, test file paths, grading, thresholds-as-test, or the
   reference answer.
5. `solution_md` is a RUNNABLE reference solution (a sequence of bash commands
   in a ```bash block) that, run on the fresh container, makes the tests pass.
   It is graded automatically, so it must actually work — not be prose.
   SELF-CONSISTENCY: the reference solution MUST satisfy the task's own stated
   threshold/spec — the metric it achieves must meet the threshold you set, its
   output must exactly match what an exact_text test asserts, and every command
   must exist and run without error. A reference that fails its own tests is the
   single most common defect: do not set a threshold higher than your reference
   reaches, and do not call tools/APIs you are unsure exist in the image.
6. Verifier kind:
   - exact_text: tests assert exact file/stdout content against a reference.
   - metric_threshold: tests compute a numeric metric vs. a reference and
     assert `metric >= threshold`. The threshold must require real work but be
     achievable by a sound approach. Ship at least 30 held-out test items so the
     agent cannot clear the bar by eyeballing inputs and hardcoding outputs.
7. `fixture_files` are extra build-context files your Dockerfile COPYs into the
   image (input data the agent works on). Do not put the answer key here.
"""


def _describe_signature(sig: Signature, axes: dict) -> str:
    tc = axes["task_complexity"].get("descriptions", {}).get(sig.task_complexity, "")
    cc = axes["command_complexity"].get("descriptions", {}).get(sig.command_complexity, "")
    skills = "\n".join(f"    - {s}" for s in sig.primitive_skills)
    return (
        f"- domain: {sig.domain}\n"
        f"- skill_type: {sig.skill_type}\n"
        f"- primitive_skills (the solution must genuinely exercise each):\n{skills}\n"
        f"- persona (write task_md as this user would phrase the request): {sig.persona}\n"
        f"- language (prefer this for any code the task needs): {sig.language}\n"
        f"- task_complexity: {sig.task_complexity} — {tc}\n"
        f"- command_complexity: {sig.command_complexity} — {cc}\n"
        f"- fixture: {sig.fixture}\n"
        f"- verifier: {sig.verifier}"
    )


def _load_exemplar(verifier: str) -> str:
    path = EXEMPLARS_DIR / f"{verifier}.json"
    # Compact JSON keeps the few-shot example unambiguous and token-cheap.
    return json.dumps(json.loads(path.read_text()), separators=(",", ":"))


def build_user_prompt(sig: Signature, axes: dict) -> str:
    image, installed = base_image_for(sig.domain)
    exemplar = _load_exemplar(sig.verifier)
    return (
        "Generate one task for this signature:\n\n"
        f"{_describe_signature(sig, axes)}\n\n"
        f"Base image: {image}\n"
        f"Already installed (do not reinstall): {installed}\n\n"
        f"Here is a complete worked example for a `{sig.verifier}` task, in the "
        f"exact JSON output format you must produce:\n\n{exemplar}\n\n"
        "Now produce the JSON object for the signature above. Make it a genuinely "
        "different task (different domain content and data), not a paraphrase of "
        "the example. Output only the JSON object."
    )
