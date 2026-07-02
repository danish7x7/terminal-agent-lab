import urllib.request
from pathlib import Path


def test_file_content():
    assert Path("/srv/data/hello.txt").read_text() == "hello from the sandbox\n"


def test_server_responds():
    with urllib.request.urlopen("http://localhost:8000/hello.txt", timeout=5) as resp:
        assert resp.status == 200
        assert resp.read().decode() == "hello from the sandbox\n"
