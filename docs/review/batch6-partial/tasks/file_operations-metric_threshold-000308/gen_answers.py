import hashlib
from pathlib import Path

records_dir = Path('/data/records')

# Simulate: replace placeholder, deduplicate, collect surviving files
files = {}
for f in sorted(records_dir.glob('*.txt')):
    content = f.read_text().replace('EXPORT_DATE: UNKNOWN', 'EXPORT_DATE: 2024-01-15')
    files[f.name] = content.encode()

# Deduplicate: keep lex-first per hash
hash_to_name = {}
for name in sorted(files.keys()):
    h = hashlib.sha256(files[name]).hexdigest()
    if h not in hash_to_name:
        hash_to_name[h] = name

# Output manifest lines sorted by filename
result = []
for name in sorted(hash_to_name.values()):
    h = hashlib.sha256(files[name]).hexdigest()
    result.append(f'{h}  {name}')

print('\n'.join(result))
