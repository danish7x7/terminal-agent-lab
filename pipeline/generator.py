"""Generate one task per signature: prompt a strong model, parse its single
JSON object, and materialize a task directory.

Validity gates (build/pre-solved/leak/solvable) live separately in the gate;
this module only produces the candidate task dir plus its signature.yaml.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import json5
import yaml

from pipeline.generator_prompt import SYSTEM_PROMPT, build_user_prompt
from pipeline.sampler import Signature, load_axes

_REQUIRED_KEYS = {"task_md", "dockerfile", "tests", "solution_md"}


class GeneratorError(RuntimeError):
    def __init__(self, message: str, detail: dict | None = None):
        super().__init__(message)
        self.detail = detail or {}


def classify_generation_failure(reply, client, exc: Exception) -> dict:
    """Label a failed generation so batches self-diagnose: truncation (hit the
    token ceiling) vs malformed-but-complete JSON, plus the parse-error type."""
    ceiling = getattr(client, "max_tokens", None)
    truncated = ceiling is not None and reply.output_tokens >= ceiling
    msg = str(exc)
    if "Unterminated string" in msg:
        etype = "unterminated_string"
    elif "property name" in msg:
        etype = "expecting_property_name"
    elif "Extra data" in msg:
        etype = "extra_data"
    elif "escape" in msg:
        etype = "invalid_escape"
    elif "missing keys" in msg or "no tests" in msg:
        etype = "schema"
    elif "no JSON object" in msg:
        etype = "no_json_object"
    else:
        etype = "other"
    return {
        "cause": "truncation" if truncated else "malformed_json",
        "parse_error_type": etype,
        "error": msg,
        "output_tokens": reply.output_tokens,
        "max_tokens": ceiling,
        "raw_tail": reply.text[-800:],
    }


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
    # Fallback chain, cheapest first:
    #  1. strict=False raw_decode — tolerates literal control chars in strings;
    #  2. + escape repair — fixes lone shell/regex backslashes (\d, \.);
    #  3. json5 — tolerates the malformed-but-complete cases models actually
    #     emit (trailing commas, // comments, unquoted keys), string-aware so it
    #     won't corrupt content the way a regex would.
    decoder = json.JSONDecoder(strict=False)
    data = None
    last_exc: Exception | None = None
    for source in (body, _repair_json_escapes(body)):
        try:
            data, _ = decoder.raw_decode(source)
            break
        except json.JSONDecodeError as exc:
            last_exc = exc
    if data is None:
        try:
            data = json5.loads(body[: body.rfind("}") + 1])
        except Exception as exc:  # noqa: BLE001 - json5 raises varied types
            raise GeneratorError(f"generation was not valid JSON: {last_exc or exc}") from exc
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
    try:
        data = parse_generation(reply.text)
    except GeneratorError as exc:
        raise GeneratorError(str(exc), detail=classify_generation_failure(reply, client, exc)) from exc
    return materialize_task(data, Path(dest_root) / task_id(sig), sig)
