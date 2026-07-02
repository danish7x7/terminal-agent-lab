from pathlib import Path


def test_greeting_content():
    assert Path("/app/greeting.txt").read_text() == "Hello, terminal agent!\n"
