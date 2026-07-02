from pathlib import Path

EXPECTED = "region,total\neast,7.00\nnorth,15.00\nsouth,5.00\n"


def test_summary_exists():
    assert Path("/output/summary.csv").exists()


def test_summary_content():
    assert Path("/output/summary.csv").read_text() == EXPECTED
