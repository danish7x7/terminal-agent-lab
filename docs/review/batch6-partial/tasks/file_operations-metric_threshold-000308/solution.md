```bash
cat > /app/dedup.py <<'PY'
import hashlib
from pathlib import Path

records_dir = Path('/data/records')
output_path = Path('/output/manifest.txt')

# Step 1: Replace placeholder in all .txt files
for f in sorted(records_dir.glob('*.txt')):
    content = f.read_text()
    new_content = content.replace('EXPORT_DATE: UNKNOWN', 'EXPORT_DATE: 2024-01-15')
    f.write_text(new_content)

# Step 2: Deduplicate by SHA-256 hash, keep lexicographically first filename
hash_to_file = {}
for f in sorted(records_dir.glob('*.txt')):
    content = f.read_bytes()
    h = hashlib.sha256(content).hexdigest()
    if h not in hash_to_file:
        hash_to_file[h] = f
    else:
        f.unlink()

# Step 3: Generate manifest sorted by filename
manifest_lines = []
for f in sorted(records_dir.glob('*.txt')):
    content = f.read_bytes()
    h = hashlib.sha256(content).hexdigest()
    manifest_lines.append(f'{h}  {f.name}')

output_path.write_text('\n'.join(manifest_lines) + '\n')
PY
python3 /app/dedup.py
pytest /tests/test_manifest.py -v
```