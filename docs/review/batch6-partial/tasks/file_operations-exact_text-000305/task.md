# Recovering Mis-named Files

You have two directories of text files:
- `/data/backup/` — your original, correctly-named archive
- `/data/current/` — a batch of mis-named or duplicated files collected later

A local manifest service is available at `http://localhost:8765/manifest.json`. **Start it first** (it serves `/data/manifest.json` over HTTP), then complete the following workflow and write results to `/output/report.txt`.

## Workflow

1. **Start the manifest service**: serve `/data/` on port 8765 using Python's built-in HTTP server (background it).

2. **Fetch the manifest** from `http://localhost:8765/manifest.json`. It maps canonical basenames to their MD5 hashes.

3. **Compare directory trees**: list every filename (basename only, no path) that appears in `/data/backup/` but NOT in `/data/current/`, and every filename in `/data/current/` but NOT in `/data/backup/`. These are the "only-in-backup" and "only-in-current" sets.

4. **Deduplicate by content hash**: compute the MD5 of every file in both directories combined. Keep exactly one representative file per unique hash (choose the file whose basename comes first alphabetically). Collect the full paths of these representatives.

5. **Count lines, words, and bytes** across all representative files combined (same order and flags as `wc -lwc`).

6. **Write `/output/report.txt`** with exactly this format (no extra blank lines, no trailing spaces):

```
only_in_backup: <comma-separated sorted basenames or NONE>
only_in_current: <comma-separated sorted basenames or NONE>
unique_files: <count of representative files>
total_lines: <N>
total_words: <N>
total_bytes: <N>
```

All comma-separated lists must be sorted alphabetically. Use `NONE` if a set is empty.
