import hashlib
from pathlib import Path

THRESHOLD = 0.80


def _score():
    manifest_path = Path('/output/manifest.txt')
    answer_path = Path('/tests/answers.txt')
    if not manifest_path.exists():
        return 0.0
    pred_lines = [l.strip() for l in manifest_path.read_text().splitlines() if l.strip()]
    gold_lines = [l.strip() for l in answer_path.read_text().splitlines() if l.strip()]
    if not gold_lines:
        return 0.0
    gold_set = set(gold_lines)
    correct = sum(1 for l in pred_lines if l in gold_set)
    return correct / len(gold_lines)


def test_manifest_score():
    assert _score() >= THRESHOLD
