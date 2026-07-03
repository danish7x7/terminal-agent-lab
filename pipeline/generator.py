"""Generate one task per signature: prompt a strong model, parse its single
JSON object, and materialize a task directory.

Validity gates (build/pre-solved/leak/solvable) live separately in the gate;
this module only produces the candidate task dir plus its signature.yaml.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from pipeline.generator_prompt import SYSTEM_PROMPT, build_user_prompt
from pipeline.sampler import Signature, load_axes

_REQUIRED_KEYS = {"task_md", "dockerfile", "tests", "solution_md"}


class GeneratorError(RuntimeError):
    pass


_VALID_ESCAPE = re.compile(r'\\(?:["\\/bfnrtu]|u[0-9a-fA-F]{4})')


def _repair_json_escapes(s: str) -> str:
    """Double lone backslashes that aren't valid JSON escapes.

    Models routinely emit shell/regex backslashes (`\\d`, `\\.`, `\\(`) inside
    string values without doubling them, which is invalid JSON. We leave valid
    escapes (\\n, \\", \\uXXXX, and already-doubled \\\\) untouched and repair
    only the lone ones, so a correct generation is unchanged.
    """
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\\":
            m = _VALID_ESCAPE.match(s, i)
            if m:
                out.append(m.group())
                i = m.end()
                continue
            out.append("\\\\")
            i += 1
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def parse_generation(text: str) -> dict:
    """Extract the task JSON from a model reply.

    We parse the first balanced JSON object starting at the first `{`, via
    json.raw_decode, rather than matching a ```json fence or an outermost
    {...} span. Two real failure modes drove this: (1) the task JSON always
    contains triple-backticks (solution_md ships a ```bash block), so fence
    matching truncates at the first inner backtick; (2) trailing prose after
    the object often contains a `}`, so a first-`{`-to-last-`}` span overshoots
    into "Extra data". raw_decode stops at the object's real close and ignores
    anything after.
    """
    start = text.find("{")
    if start == -1:
        raise GeneratorError("generation contained no JSON object")
    body = text[start:]
    # strict=False tolerates literal control chars (raw newlines/tabs) in
    # strings; the escape-repair fallback fixes lone shell/regex backslashes.
    decoder = json.JSONDecoder(strict=False)
    try:
        data, _ = decoder.raw_decode(body)
    except json.JSONDecodeError:
        try:
            data, _ = decoder.raw_decode(_repair_json_escapes(body))
        except json.JSONDecodeError as exc:
            raise GeneratorError(f"generation was not valid JSON: {exc}") from exc
    missing = _REQUIRED_KEYS - data.keys()
    if missing:
        raise GeneratorError(f"generation missing keys: {sorted(missing)}")
    if not isinstance(data["tests"], dict) or not data["tests"]:
        raise GeneratorError("generation has no tests")
    # fixture_files is optional — a task with no input files is valid.
    data.setdefault("fixture_files", {})
    if not isinstance(data["fixture_files"], dict):
        raise GeneratorError("fixture_files must be an object")
    return data


def task_id(sig: Signature) -> str:
    return f"{sig.domain}-{sig.verifier}-{sig.seed:06d}"


def materialize_task(data: dict, dest: str | Path, sig: Signature) -> Path:
    """Write a candidate task dir. `solution.md` and `signature.yaml` stay in the
    dir but are never referenced by the Dockerfile, so they never enter the image.
    """
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "task.md").write_text(data["task_md"])
    (dest / "Dockerfile").write_text(data["dockerfile"])
    (dest / "solution.md").write_text(data["solution_md"])
    (dest / "signature.yaml").write_text(yaml.safe_dump(sig.to_dict(), sort_keys=False))

    tests = dest / "tests"
    tests.mkdir(exist_ok=True)
    for name, content in data["tests"].items():
        _write_child(tests, name, content)
    for name, content in data["fixture_files"].items():
        _write_child(dest, name, content)
    return dest


def _write_child(root: Path, name: str, content: str) -> None:
    """Write `name` under `root`, refusing paths that escape it."""
    target = (root / name).resolve()
    if not str(target).startswith(str(root.resolve())):
        raise GeneratorError(f"unsafe path in generation: {name!r}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def generate_task(sig: Signature, client, axes: dict | None = None, dest_root: str | Path = "tasks") -> Path:
    """Prompt `client` for one task and materialize it under dest_root/<task_id>.

    `client` is any object with `.chat(system, messages) -> reply` where
    `reply.text` is the model output (see harness.llm.make_client).
    """
    if axes is None:
        axes = load_axes()
    user_prompt = build_user_prompt(sig, axes)
    reply = client.chat(SYSTEM_PROMPT, [{"role": "user", "content": user_prompt}])
    data = parse_generation(reply.text)
    return materialize_task(data, Path(dest_root) / task_id(sig), sig)
