```bash
cat > /app/audit.py << 'EOF'
import glob
import os
import tarfile

log_files = sorted(glob.glob('/srv/logs/*.log'))

total_lines = 0
total_words = 0
total_bytes = 0

for path in log_files:
    with open(path, 'rb') as f:
        data = f.read()
    total_bytes += len(data)
    text = data.decode('utf-8')
    lines = text.splitlines()
    total_lines += len(lines)
    for line in lines:
        total_words += len(line.split())

with open('/output/audit.txt', 'w') as f:
    f.write(f'files={len(log_files)}\n')
    f.write(f'lines={total_lines}\n')
    f.write(f'words={total_words}\n')
    f.write(f'bytes={total_bytes}\n')

with tarfile.open('/output/archive.tar', 'w') as tf:
    for path in log_files:
        tf.add(path, arcname=os.path.basename(path))

os.chmod('/output/archive.tar', 0o640)
os.chown('/output/archive.tar', 0, 0)
EOF
python3 /app/audit.py
```