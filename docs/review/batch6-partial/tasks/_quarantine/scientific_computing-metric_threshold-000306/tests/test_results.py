import pytest
from pathlib import Path
import math

THRESHOLD = 0.70

REF_FILE = Path(__file__).with_name('answers.txt')

def _load(path):
    lines = Path(path).read_text().strip().split('\n')
    return [float(x) for x in lines]

def _score():
    out = Path('/output/results.txt')
    if not out.exists():
        return 0.0
    try:
        preds = _load(out)
    except Exception:
        return 0.0
    refs = _load(REF_FILE)
    if len(preds) != len(refs):
        return 0.0
    correct = 0
    tols = [0.02, 0.02, 0.10, 0.10, 0.30, 0.10]
    for p, r, tol in zip(preds, refs, tols):
        if r == 0:
            if abs(p) < 1e-6:
                correct += 1
        elif abs(p - r) / abs(r) <= tol:
            correct += 1
    return correct / len(refs)

def test_results_accurate():
    score = _score()
    assert score >= THRESHOLD, f'Score {score:.3f} < threshold {THRESHOLD}'
