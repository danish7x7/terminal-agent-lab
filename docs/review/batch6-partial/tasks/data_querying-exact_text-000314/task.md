You are an auditor reconciling transaction records from two internal systems.

**Input files:**
- `/data/system_a.csv` — exports from System A with columns: `tx_id,date,account,amount,status`
- `/data/system_b.csv` — exports from System B with columns: `ref_id,value_date,account,amount,category`

Both files have a header row. Amounts are in cents (integers). Only consider rows where `status` is `cleared` (System A) and `category` is not `void` (System B).

Produce `/output/reconciliation.json` with exactly this structure (keys in this order, values computed from the filtered data):

```json
{
  "only_in_a": [<sorted list of tx_ids present in filtered A but absent from filtered B>],
  "only_in_b": [<sorted list of ref_ids present in filtered B but absent from filtered A>],
  "matched": [<sorted list of ids present in both with identical amounts>],
  "amount_mismatch": [<sorted list of ids present in both but with differing amounts>],
  "total_unmatched_gap": <sum of abs(amount_A - amount_B) for amount_mismatch ids>
}
```

All ID lists must be sorted lexicographically. The JSON must be valid with no trailing whitespace on lines and a final newline.

Write the result to `/output/reconciliation.json`.