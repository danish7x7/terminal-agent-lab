from pathlib import Path

def test_result_exact():
    p = Path('/output/result.txt')
    assert p.exists(), 'solution did not write /output/result.txt'
    assert p.read_text() == 'SECURE_PAYLOAD_d4e9b2f1\n'
