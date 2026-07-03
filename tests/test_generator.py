"""Generator tests: prompt rendering, JSON parsing, task materialization.
No API calls — a fake client returns a canned generation."""

import json
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from pipeline.generator import (
    GeneratorError,
    generate_task,
    materialize_task,
    parse_generation,
    task_id,
)
from pipeline.generator_prompt import SYSTEM_PROMPT, build_user_prompt
from pipeline.sampler import load_axes, sample_signature

AXES = load_axes()


def _sig(seed=1):
    return sample_signature(seed, AXES)


CANNED = {
    "task_md": "Do the thing and write /output/result.txt.",
    "dockerfile": "FROM python:3.11-slim\nRUN mkdir -p /output\n",
    "tests": {"test_it.py": "def test_it():\n    assert True\n", "answers.txt": "42\n"},
    "solution_md": "```bash\necho 42 > /output/result.txt\n```",
    "fixture_files": {"data/input.txt": "raw\n"},
}


@dataclass
class FakeReply:
    text: str


@dataclass
class FakeClient:
    payload: str

    def __post_init__(self):
        self.calls = []

    def chat(self, system, messages):
        self.calls.append((system, messages))
        return FakeReply(self.payload)


# ---- prompt rendering ----

def test_user_prompt_includes_signature_and_exemplar():
    sig = _sig(3)
    prompt = build_user_prompt(sig, AXES)
    assert sig.domain in prompt
    assert sig.persona in prompt
    for skill in sig.primitive_skills:
        assert skill in prompt
    # the matching exemplar is embedded as few-shot
    assert sig.verifier in prompt
    assert "python:3.11-slim" in prompt


def test_system_prompt_states_key_invariants():
    assert "SINGLE, STRICT JSON object" in SYSTEM_PROMPT
    assert "30 held-out" in SYSTEM_PROMPT          # metric_threshold rule
    assert "no network at runtime" in SYSTEM_PROMPT.lower() or "no network" in SYSTEM_PROMPT.lower()
    assert "NEVER mention tests" in SYSTEM_PROMPT


# ---- parsing ----

def test_parse_plain_json():
    data = parse_generation(json.dumps(CANNED))
    assert data["task_md"].startswith("Do the thing")


def test_parse_json_in_fence():
    data = parse_generation("Here you go:\n```json\n" + json.dumps(CANNED) + "\n```\n")
    assert data["tests"]["answers.txt"] == "42\n"


def test_parse_json_with_surrounding_prose():
    data = parse_generation("sure!\n" + json.dumps(CANNED) + "\nhope that helps")
    assert set(data) >= {"task_md", "dockerfile", "tests"}


def test_parse_trailing_prose_containing_brace():
    # Real failure mode: model appends an explanation that itself has a '}',
    # which a first-{-to-last-} span would swallow into "Extra data".
    text = json.dumps(CANNED) + "\n\nNote: the reward is 1.0 when {all tests pass}."
    data = parse_generation(text)
    assert data["task_md"].startswith("Do the thing")


def test_parse_solution_backticks_survive():
    data = parse_generation("```json\n" + json.dumps(CANNED) + "\n```")
    assert "```bash" in data["solution_md"]


def test_parse_json5_fallback_trailing_comma():
    # malformed-but-complete: trailing comma before } — json5 fallback handles it.
    raw = (
        '{"task_md":"t","dockerfile":"d",'
        '"tests":{"test_x.py":"x",},'
        '"solution_md":"s","fixture_files":{},}'
    )
    data = parse_generation(raw)
    assert data["tests"]["test_x.py"] == "x"


def test_parse_json5_fallback_line_comment():
    raw = (
        "{\n"
        '  "task_md":"t", // the instructions\n'
        '  "dockerfile":"d",\n'
        '  "tests":{"test_x.py":"x"},\n'
        '  "solution_md":"s","fixture_files":{}\n'
        "}"
    )
    data = parse_generation(raw)
    assert data["dockerfile"] == "d"


def test_classify_failure_flags_truncation():
    from dataclasses import dataclass

    @dataclass
    class R:
        text: str
        output_tokens: int

    @dataclass
    class C:
        max_tokens: int

    from pipeline.generator import classify_generation_failure

    exc = __import__("json").JSONDecodeError("Unterminated string", "x", 0)
    d = classify_generation_failure(R("...abc", output_tokens=8192), C(8192), exc)
    assert d["cause"] == "truncation"
    assert d["parse_error_type"] == "unterminated_string"

    d2 = classify_generation_failure(R("...abc", output_tokens=4000), C(8192), exc)
    assert d2["cause"] == "malformed_json"


def test_parse_repairs_invalid_shell_backslash_escapes():
    # Real failure mode: model ships a regex/awk backslash un-doubled inside a
    # JSON string, which is an invalid JSON escape until repaired.
    raw = (
        '{"task_md":"t","dockerfile":"d",'
        '"tests":{"test_x.py":"import re\\nassert re.match(r\'\\d+\', \'42\')"},'
        '"solution_md":"s","fixture_files":{}}'
    )
    data = parse_generation(raw)
    assert "\\d+" in data["tests"]["test_x.py"]  # decodes to a literal \d+


def test_repair_leaves_valid_escapes_untouched():
    from pipeline.generator import _repair_json_escapes

    assert _repair_json_escapes(r'"a\nb"') == r'"a\nb"'
    assert _repair_json_escapes(r'"a\\d"') == r'"a\\d"'      # already doubled
    assert _repair_json_escapes(r'"a\db"') == r'"a\\db"'     # lone -> doubled
    assert _repair_json_escapes(r'"é"') == r'"é"'


def test_parse_rejects_non_json():
    with pytest.raises(GeneratorError, match="no JSON object"):
        parse_generation("no json here")


def test_parse_rejects_missing_keys():
    with pytest.raises(GeneratorError, match="missing keys"):
        parse_generation(json.dumps({"task_md": "x"}))


def test_parse_rejects_empty_tests():
    bad = {**CANNED, "tests": {}}
    with pytest.raises(GeneratorError, match="no tests"):
        parse_generation(json.dumps(bad))


def test_parse_defaults_missing_fixture_files_to_empty():
    payload = {k: v for k, v in CANNED.items() if k != "fixture_files"}
    data = parse_generation(json.dumps(payload))
    assert data["fixture_files"] == {}


# ---- materialization ----

def test_materialize_writes_expected_layout(tmp_path):
    sig = _sig(5)
    dest = materialize_task(CANNED, tmp_path / "t", sig)
    assert (dest / "task.md").read_text().startswith("Do the thing")
    assert (dest / "Dockerfile").exists()
    assert (dest / "solution.md").exists()
    assert (dest / "tests" / "test_it.py").exists()
    assert (dest / "tests" / "answers.txt").read_text() == "42\n"
    assert (dest / "data" / "input.txt").read_text() == "raw\n"


def test_materialize_writes_roundtrippable_signature(tmp_path):
    sig = _sig(9)
    dest = materialize_task(CANNED, tmp_path / "t", sig)
    loaded = yaml.safe_load((dest / "signature.yaml").read_text())
    assert loaded["seed"] == sig.seed
    assert loaded["domain"] == sig.domain


def test_dockerfile_never_copies_answer_key(tmp_path):
    # Structural check of the design rule: the answer key is under tests/, and
    # the Dockerfile does not COPY from tests/.
    sig = _sig(2)
    dest = materialize_task(CANNED, tmp_path / "t", sig)
    dockerfile = (dest / "Dockerfile").read_text()
    assert "answers.txt" not in dockerfile
    assert "tests/" not in dockerfile


def test_materialize_rejects_path_escape(tmp_path):
    evil = {**CANNED, "fixture_files": {"../escape.txt": "x"}}
    with pytest.raises(GeneratorError, match="unsafe path"):
        materialize_task(evil, tmp_path / "t", _sig())


def test_task_id_is_stable_and_descriptive():
    sig = _sig(7)
    assert task_id(sig) == f"{sig.domain}-{sig.verifier}-000007"


def test_generate_task_end_to_end_with_fake_client(tmp_path):
    sig = _sig(4)
    client = FakeClient(json.dumps(CANNED))
    dest = generate_task(sig, client, AXES, dest_root=tmp_path)
    assert dest == tmp_path / task_id(sig)
    assert (dest / "task.md").exists()
    # the client was asked with our system prompt
    assert client.calls[0][0] == SYSTEM_PROMPT
