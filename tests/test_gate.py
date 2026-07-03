"""Gate unit tests for the pure helpers (bucketing, generation round-trip,
repair prompt, leak-needle selection, finalize/move). The full A->B->B'->L->C
path needs Docker + API and is exercised by the smoke batch, not here."""

import json
from dataclasses import dataclass

import pytest
import yaml

from pipeline.gate import (
    GateResult,
    _distinctive_needles,
    _finalize,
    bucket_subdir,
    build_repair_prompt,
    read_generation,
)
from pipeline.generator import materialize_task
from pipeline.sampler import load_axes, sample_signature

AXES = load_axes()
CANNED = {
    "task_md": "Write /output/result.txt.",
    "dockerfile": "FROM python:3.11-slim\nRUN mkdir -p /output\n",
    "tests": {
        "test_it.py": "def test_it():\n    assert open('/output/result.txt').read().strip() == 'the-secret-value-1234'\n",
        "answers.txt": "the-distinctive-answer-line\nshort\n",
    },
    "solution_md": "```bash\necho hi > /output/result.txt\n```",
    "fixture_files": {"data/input.txt": "raw\n"},
}


def _sig(seed=1):
    return sample_signature(seed, AXES)


def test_bucket_subdir_mapping():
    assert bucket_subdir("admitted") == ""
    assert bucket_subdir("unsolved") == "_unsolved"
    assert bucket_subdir("quarantined") == "_quarantine"


def test_read_generation_round_trips(tmp_path):
    dest = materialize_task(CANNED, tmp_path / "t", _sig())
    gen = read_generation(dest)
    assert gen["task_md"] == CANNED["task_md"]
    assert gen["tests"]["answers.txt"] == CANNED["tests"]["answers.txt"]
    assert gen["fixture_files"]["data/input.txt"] == "raw\n"
    # meta files never leak into the reconstructed fixtures
    assert "signature.yaml" not in gen["fixture_files"]
    assert "solution.md" not in gen["fixture_files"]


def test_build_repair_prompt_carries_execution_feedback():
    prompt = build_repair_prompt(CANNED, "E assert 0.36 >= 0.72\n1 failed")
    assert "0.36 >= 0.72" in prompt
    assert "execution feedback" in prompt.lower()
    assert "must STILL fail" in prompt  # keeps the not-pre-solved invariant


def test_distinctive_needles_skip_short_and_keep_long(tmp_path):
    dest = materialize_task(CANNED, tmp_path / "t", _sig())
    needles = _distinctive_needles(dest)
    assert "the-distinctive-answer-line" in needles   # >= 8 chars, from answers.txt
    assert "the-secret-value-1234" in needles         # string literal in the test
    assert "short" not in needles                      # < 8 chars, skipped


def test_finalize_moves_dir_and_writes_gate_json(tmp_path):
    src = materialize_task(CANNED, tmp_path / "cand" / "mytask", _sig())
    res = GateResult(task_id="mytask", gate_B_reward=0.0, gate_B_prime_reward=1.0)
    out = _finalize(res, "quarantined", "broken_test", src, tmp_path / "tasks")
    moved = tmp_path / "tasks" / "_quarantine" / "mytask"
    assert not src.exists()
    assert moved.exists()
    assert out.destination == str(moved)
    gate = json.loads((moved / "gate.json").read_text())
    assert gate["verdict"] == "quarantined"
    assert gate["reason"] == "broken_test"


def test_finalize_admitted_lands_in_tasks_root(tmp_path):
    src = materialize_task(CANNED, tmp_path / "cand" / "good", _sig())
    _finalize(GateResult(task_id="good"), "admitted", None, src, tmp_path / "tasks")
    assert (tmp_path / "tasks" / "good").exists()
    assert not (tmp_path / "tasks" / "_quarantine").exists()
