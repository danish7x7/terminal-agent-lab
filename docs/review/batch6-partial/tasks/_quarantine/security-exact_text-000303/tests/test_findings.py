from pathlib import Path


def test_findings_exact():
    p = Path('/output/findings.txt')
    assert p.exists(), 'solution did not write /output/findings.txt'
    content = p.read_text()
    expected = 'PCAPTOKEN=s3cr3tXY\nBRUTEPASS=sunshine\nBADPERM=/data/configs/db.conf\nANOMALY_IP=192.168.1.55\n'
    assert content == expected, f'Got:\n{content!r}\nExpected:\n{expected!r}'
