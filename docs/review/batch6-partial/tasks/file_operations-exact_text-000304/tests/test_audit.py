import os
import tarfile
from pathlib import Path


def test_audit_txt_content():
    p = Path('/output/audit.txt')
    assert p.exists(), '/output/audit.txt does not exist'
    assert p.read_text() == 'files=3\nlines=21\nwords=173\nbytes=1353\n'


def test_archive_exists():
    p = Path('/output/archive.tar')
    assert p.exists(), '/output/archive.tar does not exist'


def test_archive_contains_log_files():
    with tarfile.open('/output/archive.tar', 'r') as tf:
        names = sorted(tf.getnames())
    assert names == ['access.log', 'app.log', 'error.log'], f'unexpected archive members: {names}'


def test_archive_permissions():
    st = os.stat('/output/archive.tar')
    mode = oct(st.st_mode & 0o777)
    assert mode == '0o640', f'expected 0o640, got {mode}'


def test_archive_owner():
    st = os.stat('/output/archive.tar')
    assert st.st_uid == 0, f'expected uid 0, got {st.st_uid}'
    assert st.st_gid == 0, f'expected gid 0, got {st.st_gid}'
