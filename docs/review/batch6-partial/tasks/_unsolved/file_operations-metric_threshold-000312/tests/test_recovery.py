import os
import hashlib
from pathlib import Path

THRESHOLD = 0.55
REFERENCE_DIR = Path('/workspace/reference')
CLEAN_DIR = Path('/workspace/clean')
REPORT = Path('/workspace/report.txt')


def file_hash(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_report_exists():
    assert REPORT.exists(), 'report.txt not found'


def test_clean_dir_exists():
    assert CLEAN_DIR.exists(), '/workspace/clean not found'


def test_match_threshold():
    ref_files = {f.name: f for f in REFERENCE_DIR.iterdir() if f.is_file()}
    if not REPORT.exists():
        assert False, 'report.txt missing'

    report_lines = REPORT.read_text().strip().splitlines()
    match_names = set()
    for line in report_lines:
        parts = line.strip().split()
        if len(parts) == 2 and parts[0] == 'MATCH':
            match_names.add(parts[1])

    # Verify MATCH files are actually in clean dir with correct content
    verified_matches = 0
    for fname in match_names:
        clean_file = CLEAN_DIR / fname
        ref_file = ref_files.get(fname)
        if clean_file.exists() and ref_file and file_hash(clean_file) == file_hash(ref_file):
            verified_matches += 1

    ratio = verified_matches / len(ref_files) if ref_files else 0.0
    assert ratio >= THRESHOLD, (
        f'Only {verified_matches}/{len(ref_files)} files correctly recovered '
        f'({ratio:.2%} < {THRESHOLD:.0%})'
    )


def test_report_format():
    if not REPORT.exists():
        return
    valid_prefixes = {'MATCH', 'MISMATCH_NAME', 'MISMATCH_CONTENT'}
    for line in REPORT.read_text().strip().splitlines():
        parts = line.strip().split()
        assert len(parts) == 2, f'Bad line format: {line!r}'
        assert parts[0] in valid_prefixes, f'Unknown prefix: {parts[0]}'
