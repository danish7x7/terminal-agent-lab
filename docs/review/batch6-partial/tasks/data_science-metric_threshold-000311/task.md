You are an analyst building a quick baseline model for customer churn prediction.

You have two datasets:
- `/data/transactions.csv` — daily transaction records with columns: `customer_id, date, amount, n_items`
- `/data/labels.csv` — churn labels with columns: `customer_id, churned` (1 = churned, 0 = retained)

Your job is to build a feature matrix, train a simple classifier, and write predictions, but also produce a detailed feature analysis report.

**Step 1 — Feature Engineering**: For each customer aggregate over the transaction history:
- `mean_amount`, `median_amount`, `q25_amount`, `q75_amount` (descriptive stats on `amount`)
- `mean_items`, `median_items` (descriptive stats on `n_items`)
- `ma7_last` — the last value of a 7-day moving average of daily total `amount` (sort by date, resample to daily, fill missing days with 0, then compute rolling mean with window=7, take the final value)
- `n_transactions` — total transaction count
- `amount_std` — standard deviation of `amount` (use 0 if only one transaction)

**Step 2 — Train a classifier** on customers in `/data/labels.csv` using the features above. Produce predictions for ALL customers in labels.csv.

**Step 3 — Confusion matrix**: Compute the confusion matrix (TP, FP, TN, FN) of your predictions vs true labels. Write `/output/confusion_matrix.txt` with exactly 4 lines:
```
TP=<int>
FP=<int>
TN=<int>
FN=<int>
```

**Step 4 — Histogram summary**: Compute a 5-bin histogram of `mean_amount` across all customers. Write `/output/histogram.txt` with exactly 5 lines, each `<bin_left>-<bin_right>:<count>` (round bin edges to 2 decimal places, counts are integers).

**Step 5 — Moving average series**: For customer `C001`, write the full 7-day moving average series (one value per calendar day from their first to last transaction date, daily totals, rolling window=7, fill gaps with 0) to `/output/ma7_C001.txt`, one float per line rounded to 4 decimal places.

All output files must exist at `/output/`. Predictions accuracy is scored; aim for F1 >= 0.72 on the labeled set.