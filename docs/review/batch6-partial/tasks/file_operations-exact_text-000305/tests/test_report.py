from pathlib import Path

EXPECTED = (
    "only_in_backup: alpha.txt,beta.txt,gamma.txt\n"
    "only_in_current: doc_beta.txt,file1.txt,file2.txt,gamma_copy.txt,new_delta.txt\n"
    "unique_files: 4\n"
    "total_lines: 7\n"
    "total_words: 19\n"
    "total_bytes: 98\n"
)

def test_report_exact():
    p = Path('/output/report.txt')
    assert p.exists(), '/output/report.txt was not created'
    actual = p.read_text()
    assert actual == EXPECTED, f'Content mismatch.\nExpected:\n{EXPECTED!r}\nGot:\n{actual!r}'
