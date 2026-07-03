import os
from pathlib import Path


EXPECTED_MANIFEST = """bin/run.sh
config/prod.cfg
config/settings.cfg
config/settings_link.cfg
lib/helpers.py
lib/parser.py
lib/utils.py
lib/utils_link.py
tests/test_utils.py
"""


def test_manifest_exact():
    p = Path('/output/manifest.txt')
    assert p.exists(), '/output/manifest.txt does not exist'
    actual = p.read_text()
    assert actual == EXPECTED_MANIFEST, (
        f'Manifest mismatch.\nExpected:\n{EXPECTED_MANIFEST!r}\nGot:\n{actual!r}'
    )


def test_archive_exists():
    assert Path('/output/release.tar.gz').exists(), '/output/release.tar.gz does not exist'


def test_verify_dir_matches_manifest():
    base = Path('/verify/release-1.0')
    assert base.exists(), '/verify/release-1.0 does not exist after extraction'
    files = sorted(
        str(f.relative_to(base))
        for f in base.rglob('*')
        if f.is_file()
    )
    expected = [line for line in EXPECTED_MANIFEST.strip().split('\n')]
    assert files == expected, f'Files in /verify/release-1.0 do not match manifest.\nExpected: {expected}\nGot: {files}'
