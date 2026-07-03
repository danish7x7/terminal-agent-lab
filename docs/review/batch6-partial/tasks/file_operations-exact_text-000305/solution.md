```bash
# 1. Start the manifest HTTP service in background
cd /data && python3 -m http.server 8765 &
HTTP_PID=$!
sleep 1

# 2. Fetch the manifest (just to exercise the service; we use it to confirm hashes)
curl -s http://localhost:8765/manifest.json > /tmp/manifest.json
cat /tmp/manifest.json

# 3. Compare directory trees: basenames only-in-backup and only-in-current
BACKUP_NAMES=$(ls /data/backup/ | sort)
CURRENT_NAMES=$(ls /data/current/ | sort)

ONLY_IN_BACKUP=$(comm -23 <(echo "$BACKUP_NAMES") <(echo "$CURRENT_NAMES") | tr '\n' ',' | sed 's/,$//')
ONLY_IN_CURRENT=$(comm -13 <(echo "$BACKUP_NAMES") <(echo "$CURRENT_NAMES") | tr '\n' ',' | sed 's/,$//')

[ -z "$ONLY_IN_BACKUP" ] && ONLY_IN_BACKUP="NONE"
[ -z "$ONLY_IN_CURRENT" ] && ONLY_IN_CURRENT="NONE"

# 4. Deduplicate by MD5 hash across both directories combined
# Compute md5 for all files, sort by hash then by basename, pick first basename per hash
find /data/backup /data/current -maxdepth 1 -type f | while read f; do
    echo "$(md5sum "$f" | awk '{print $1}') $(basename "$f") $f"
done | sort -k1,1 -k2,2 > /tmp/all_hashes.txt

cat /tmp/all_hashes.txt

# For each unique hash, pick the file with alphabetically first basename
python3 - <<'PYEOF'
import sys

entries = []
with open('/tmp/all_hashes.txt') as f:
    for line in f:
        parts = line.strip().split(' ', 2)
        if len(parts) == 3:
            h, base, path = parts
            entries.append((h, base, path))

# Sort by hash, then by basename
entries.sort(key=lambda x: (x[0], x[1]))

seen = {}
reps = []
for h, base, path in entries:
    if h not in seen:
        seen[h] = (base, path)
        reps.append(path)

with open('/tmp/representatives.txt', 'w') as out:
    for p in sorted(reps):
        out.write(p + '\n')
PYEOF

cat /tmp/representatives.txt

# 5. Count lines, words, bytes across representative files
UNIQUE_COUNT=$(wc -l < /tmp/representatives.txt)

# Use wc on all representative files
mapfile -t REP_FILES < /tmp/representatives.txt
WC_OUT=$(wc -lwc "${REP_FILES[@]}" | tail -1)
TOTAL_LINES=$(echo $WC_OUT | awk '{print $1}')
TOTAL_WORDS=$(echo $WC_OUT | awk '{print $2}')
TOTAL_BYTES=$(echo $WC_OUT | awk '{print $3}')

# If only one file, wc doesn't print a total line; handle that
if [ "$UNIQUE_COUNT" -eq 1 ]; then
    WC_OUT=$(wc -lwc "${REP_FILES[@]}")
    TOTAL_LINES=$(echo $WC_OUT | awk '{print $1}')
    TOTAL_WORDS=$(echo $WC_OUT | awk '{print $2}')
    TOTAL_BYTES=$(echo $WC_OUT | awk '{print $3}')
fi

# 6. Write report
cat > /output/report.txt <<EOF
only_in_backup: ${ONLY_IN_BACKUP}
only_in_current: ${ONLY_IN_CURRENT}
unique_files: ${UNIQUE_COUNT}
total_lines: ${TOTAL_LINES}
total_words: ${TOTAL_WORDS}
total_bytes: ${TOTAL_BYTES}
EOF

cat /output/report.txt

# Stop the HTTP server
kill $HTTP_PID
```
