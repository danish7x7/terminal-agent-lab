```bash
cat > /app/solve.py << 'PYEOF'
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Load data
tx = pd.read_csv('/data/transactions.csv', parse_dates=['date'])
labels = pd.read_csv('/data/labels.csv')

# ---- Feature Engineering ----
features = []
for cid, grp in tx.groupby('customer_id'):
    grp = grp.sort_values('date')
    amt = grp['amount']
    items = grp['n_items']

    # descriptive stats
    mean_amount = amt.mean()
    median_amount = amt.median()
    q25_amount = amt.quantile(0.25)
    q75_amount = amt.quantile(0.75)
    mean_items = items.mean()
    median_items = items.median()
    n_transactions = len(grp)
    amount_std = amt.std(ddof=1) if len(amt) > 1 else 0.0

    # 7-day moving average: daily totals, fill gaps, rolling(7)
    daily = grp.groupby('date')['amount'].sum()
    full_range = pd.date_range(daily.index.min(), daily.index.max(), freq='D')
    daily = daily.reindex(full_range, fill_value=0.0)
    ma7 = daily.rolling(window=7, min_periods=1).mean()
    ma7_last = float(ma7.iloc[-1])

    features.append({
        'customer_id': cid,
        'mean_amount': mean_amount,
        'median_amount': median_amount,
        'q25_amount': q25_amount,
        'q75_amount': q75_amount,
        'mean_items': mean_items,
        'median_items': median_items,
        'n_transactions': n_transactions,
        'amount_std': amount_std,
        'ma7_last': ma7_last,
    })

feat_df = pd.DataFrame(features)

# ---- MA7 for C001 ----
c001 = tx[tx['customer_id'] == 'C001'].sort_values('date')
daily_c001 = c001.groupby('date')['amount'].sum()
full_range_c001 = pd.date_range(daily_c001.index.min(), daily_c001.index.max(), freq='D')
daily_c001 = daily_c001.reindex(full_range_c001, fill_value=0.0)
ma7_c001 = daily_c001.rolling(window=7, min_periods=1).mean()
with open('/output/ma7_C001.txt', 'w') as f:
    for v in ma7_c001:
        f.write(f'{v:.4f}\n')

# ---- Histogram of mean_amount ----
counts, bin_edges = np.histogram(feat_df['mean_amount'], bins=5)
with open('/output/histogram.txt', 'w') as f:
    for i in range(5):
        left = round(bin_edges[i], 2)
        right = round(bin_edges[i+1], 2)
        f.write(f'{left}-{right}:{counts[i]}\n')

# ---- Train classifier ----
merged = labels.merge(feat_df, on='customer_id')
feat_cols = ['mean_amount','median_amount','q25_amount','q75_amount',
             'mean_items','median_items','n_transactions','amount_std','ma7_last']
X = merged[feat_cols].fillna(0).values
y = merged['churned'].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

clf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
clf.fit(X_scaled, y)
preds = clf.predict(X_scaled)

# ---- Confusion matrix ----
TP = int(((preds == 1) & (y == 1)).sum())
FP = int(((preds == 1) & (y == 0)).sum())
TN = int(((preds == 0) & (y == 0)).sum())
FN = int(((preds == 0) & (y == 1)).sum())

with open('/output/confusion_matrix.txt', 'w') as f:
    f.write(f'TP={TP}\nFP={FP}\nTN={TN}\nFN={FN}\n')

print(f'TP={TP} FP={FP} TN={TN} FN={FN}')
prec = TP/(TP+FP) if TP+FP > 0 else 0
rec = TP/(TP+FN) if TP+FN > 0 else 0
f1 = 2*prec*rec/(prec+rec) if prec+rec > 0 else 0
print(f'F1={f1:.4f}')
PYEOF
python3 /app/solve.py
```