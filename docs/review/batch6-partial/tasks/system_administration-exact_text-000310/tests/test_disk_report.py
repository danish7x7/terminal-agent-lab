from pathlib import Path

def test_disk_report_exact():
    p = Path('/output/disk_report.txt')
    assert p.exists(), '/output/disk_report.txt not found'
    assert p.read_text() == 'pruned=5\nremaining=3\nowner=appuser\n'
