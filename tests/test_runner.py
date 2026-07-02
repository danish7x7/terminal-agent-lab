import json
import math

import pytest

from harness.runner import _append_jsonl, pass_at_k, summarize


def test_pass_at_k_edges():
    assert pass_at_k(4, 0, 1) == 0.0
    assert pass_at_k(4, 4, 1) == 1.0
    assert pass_at_k(4, 2, 4) == 1.0  # any success guarantees pass when k == n


def test_pass_at_k_unbiased_values():
    assert pass_at_k(4, 2, 1) == pytest.approx(0.5)
    # 1 - C(6,4)/C(8,4) = 1 - 15/70
    assert pass_at_k(8, 2, 4) == pytest.approx(1 - 15 / 70)


def test_pass_at_k_rejects_k_greater_than_n():
    with pytest.raises(ValueError):
        pass_at_k(4, 1, 8)


def test_summarize_counts_only_full_reward_as_pass():
    summary = summarize("t", "m", [1.0, 0.5, 0.0, 1.0])
    assert summary["successes"] == 2
    assert summary["mean_reward"] == pytest.approx(0.625)
    assert summary["pass_at_k"]["1"] == pytest.approx(0.5)
    assert summary["pass_at_k"]["4"] == 1.0
    assert "8" not in summary["pass_at_k"]  # only k <= n reported


def test_append_jsonl_round_trips(tmp_path):
    path = tmp_path / "out" / "r.jsonl"
    _append_jsonl(path, {"a": 1})
    _append_jsonl(path, {"b": math.pi})
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert rows == [{"a": 1}, {"b": math.pi}]
