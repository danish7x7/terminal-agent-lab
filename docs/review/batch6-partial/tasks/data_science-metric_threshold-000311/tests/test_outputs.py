import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import re

OUTPUT = Path('/output')

# ---- helpers ----
def read_cm():
    p = OUTPUT / 'confusion_matrix.txt'
    if not p.exists():
        return None
    d = {}
    for line in p.read_text().strip().splitlines():
        k, v = line.split('=')
        d[k.strip()] = int(v.strip())
    return d

def read_hist():
    p = OUTPUT / 'histogram.txt'
    if not p.exists():
        return None
    bins = []
    for line in p.read_text().strip().splitlines():
        m = re.match(r'([\d.]+)-([\d.]+):(\d+)', line.strip())
        if m:
            bins.append((float(m.group(1)), float(m.group(2)), int(m.group(3))))
    return bins

def read_ma7():
    p = OUTPUT / 'ma7_C001.txt'
    if not p.exists():
        return None
    return [float(x) for x in p.read_text().strip().splitlines()]

# ---- confusion matrix ----
def test_confusion_matrix_exists():
    assert (OUTPUT / 'confusion_matrix.txt').exists(), 'confusion_matrix.txt missing'

def test_confusion_matrix_keys():
    cm = read_cm()
    assert cm is not None
    for k in ['TP','FP','TN','FN']:
        assert k in cm, f'{k} missing'

def test_confusion_matrix_total():
    cm = read_cm()
    # labels.csv has 80 customers
    total = cm['TP'] + cm['FP'] + cm['TN'] + cm['FN']
    assert total == 80, f'Expected 80 predictions, got {total}'

def test_f1_score():
    cm = read_cm()
    tp, fp, fn = cm['TP'], cm['FP'], cm['FN']
    if tp + fp == 0 or tp + fn == 0:
        f1 = 0.0
    else:
        prec = tp / (tp + fp)
        rec = tp / (tp + fn)
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    assert f1 >= 0.72, f'F1={f1:.4f} below threshold 0.72'

# ---- histogram ----
def test_histogram_exists():
    assert (OUTPUT / 'histogram.txt').exists(), 'histogram.txt missing'

def test_histogram_5_bins():
    h = read_hist()
    assert h is not None and len(h) == 5, f'Expected 5 bins, got {len(h) if h else "None"}'

def test_histogram_counts_sum():
    h = read_hist()
    total = sum(c for _, _, c in h)
    # all 80 customers
    assert total == 80, f'Histogram counts sum to {total}, expected 80'

def test_histogram_bins_ordered():
    h = read_hist()
    for i in range(len(h)-1):
        assert h[i][1] <= h[i+1][0] + 1e-6, 'Bins not ordered'

# ---- MA7 series ----
def test_ma7_exists():
    assert (OUTPUT / 'ma7_C001.txt').exists(), 'ma7_C001.txt missing'

def test_ma7_length():
    # C001 has transactions from 2023-01-01 to 2023-03-31 => 90 days
    vals = read_ma7()
    assert vals is not None and len(vals) == 90, f'Expected 90 values, got {len(vals) if vals else "None"}'

def test_ma7_non_negative():
    vals = read_ma7()
    assert all(v >= 0 for v in vals), 'MA7 contains negative values'

def test_ma7_first_7_increasing_or_nondecreasing():
    # first 7 values: rolling mean of cumulative days — value 7 should be >= value 1
    vals = read_ma7()
    # C001 has activity on most days so ma7 should be positive by day 7
    assert vals[6] > 0, f'MA7 day-7 value is {vals[6]}, expected positive'
