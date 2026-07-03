import math
from pathlib import Path

THRESHOLD = 0.90

REF_FILE = Path(__file__).with_name('reference_answers.txt')

def parse_results(path):
    result = {}
    for line in Path(path).read_text().strip().splitlines():
        k, v = line.strip().split('=')
        result[k.strip()] = float(v.strip())
    return result

def parse_reference():
    result = {}
    for line in REF_FILE.read_text().strip().splitlines():
        k, v = line.strip().split('=')
        result[k.strip()] = float(v.strip())
    return result

def score(pred, ref):
    keys = ['A_star', 'norm_L2', 'norm_L1', 'norm_Linf']
    correct = 0
    for k in keys:
        p = pred.get(k, None)
        r = ref[k]
        if p is not None and abs(p - r) / (abs(r) + 1e-12) < 0.01:
            correct += 1
    return correct / len(keys)

def test_results_meet_threshold():
    out = Path('/output/results.txt')
    assert out.exists(), '/output/results.txt not found'
    pred = parse_results(out)
    ref = parse_reference()
    s = score(pred, ref)
    assert s >= THRESHOLD, f'Score {s:.2f} below threshold {THRESHOLD}. pred={pred}, ref={ref}'
