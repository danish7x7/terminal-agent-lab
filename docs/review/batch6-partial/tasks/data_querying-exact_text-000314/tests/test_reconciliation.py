import json
from pathlib import Path


def test_reconciliation_exact():
    p = Path('/output/reconciliation.json')
    assert p.exists(), 'solution did not write /output/reconciliation.json'
    content = p.read_text()
    data = json.loads(content)

    expected = {
        "only_in_a": ["TXA003", "TXA007", "TXA011"],
        "only_in_b": ["TXB005", "TXB009", "TXB014"],
        "matched": ["TXA001", "TXA004", "TXA006", "TXA008", "TXA010", "TXA012"],
        "amount_mismatch": ["TXA002", "TXA005", "TXA009"],
        "total_unmatched_gap": 5500
    }

    assert data["only_in_a"] == expected["only_in_a"]
    assert data["only_in_b"] == expected["only_in_b"]
    assert data["matched"] == expected["matched"]
    assert data["amount_mismatch"] == expected["amount_mismatch"]
    assert data["total_unmatched_gap"] == expected["total_unmatched_gap"]

    # Check key order and exact formatting
    lines = content.split('\n')
    assert lines[-1] == '', 'file must end with newline'
    keys = list(data.keys())
    assert keys == ["only_in_a", "only_in_b", "matched", "amount_mismatch", "total_unmatched_gap"]
