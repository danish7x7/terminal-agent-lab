```bash
mkdir -p /output

python3 - <<'PYEOF'
import json, csv

def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))

a_rows = read_csv('/data/system_a.csv')
b_rows = read_csv('/data/system_b.csv')

# Filter
a_filtered = {r['tx_id']: int(r['amount']) for r in a_rows if r['status'] == 'cleared'}
b_filtered = {r['ref_id']: int(r['amount']) for r in b_rows if r['category'] != 'void'}

a_ids = set(a_filtered.keys())
b_ids = set(b_filtered.keys())

only_in_a = sorted(a_ids - b_ids)
only_in_b = sorted(b_ids - a_ids)
common = a_ids & b_ids

matched = sorted(i for i in common if a_filtered[i] == b_filtered[i])
amount_mismatch = sorted(i for i in common if a_filtered[i] != b_filtered[i])
total_gap = sum(abs(a_filtered[i] - b_filtered[i]) for i in amount_mismatch)

result = {
    'only_in_a': only_in_a,
    'only_in_b': only_in_b,
    'matched': matched,
    'amount_mismatch': amount_mismatch,
    'total_unmatched_gap': total_gap
}

with open('/output/reconciliation.json', 'w') as f:
    json.dump(result, f, indent=2)
    f.write('\n')
PYEOF
```