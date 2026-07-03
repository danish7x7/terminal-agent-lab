```bash
#!/usr/bin/env bash
set -euo pipefail

# Step 1: Create staging area
mkdir -p /staging/release-1.0

# Step 2: Copy resolved content from /project/src preserving relative paths
# Use Python for symlink resolution to handle edge cases cleanly
python3 - <<'PYEOF'
import os
import shutil
from pathlib import Path

src = Path('/project/src')
dst = Path('/staging/release-1.0')

for root, dirs, files in os.walk(src, followlinks=False):
    root_path = Path(root)
    rel_root = root_path.relative_to(src)
    # Create corresponding directory in staging
    (dst / rel_root).mkdir(parents=True, exist_ok=True)
    for fname in files:
        fpath = root_path / fname
        # Resolve symlink; skip dangling
        try:
            resolved = fpath.resolve(strict=True)
        except (OSError, FileNotFoundError):
            continue
        if not resolved.is_file():
            continue
        dest_file = dst / rel_root / fname
        shutil.copy2(str(resolved), str(dest_file))
PYEOF

# Step 3: Remove files > 2048 bytes
find /staging/release-1.0 -type f -size +2048c -delete

# Step 4: Remove files older than 2024-01-01 00:00:00 UTC (timestamp 1704067200)
# find -newer uses a reference file; create one with that timestamp
touch -d '2024-01-01 00:00:00 UTC' /tmp/ref_date
find /staging/release-1.0 -type f ! -newer /tmp/ref_date -delete

# Step 5: Remove *.tmp and *.log files
find /staging/release-1.0 -type f \( -name '*.tmp' -o -name '*.log' \) -delete

# Step 6: Create the release archive with relative paths
mkdir -p /output
tar -czf /output/release.tar.gz -C /staging release-1.0

# Step 7: Extract into /verify
mkdir -p /verify
tar -xzf /output/release.tar.gz -C /verify

# Step 8: Write sorted manifest of regular files
python3 - <<'PYEOF'
from pathlib import Path

base = Path('/verify/release-1.0')
files = sorted(
    str(f.relative_to(base))
    for f in base.rglob('*')
    if f.is_file()
)

with open('/output/manifest.txt', 'w') as fh:
    for line in files:
        fh.write(line + '\n')
PYEOF
```