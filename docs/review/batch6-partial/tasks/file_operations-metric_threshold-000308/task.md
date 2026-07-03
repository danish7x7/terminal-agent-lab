You are an analyst deduplicating a batch of exported records.

Inside `/data/records/` there are several `.txt` files representing exported records. Some files are exact duplicates (identical content). The files also contain a placeholder string `EXPORT_DATE: UNKNOWN` that must be replaced with `EXPORT_DATE: 2024-01-15` everywhere it appears.

Your job:
1. Replace every occurrence of `EXPORT_DATE: UNKNOWN` with `EXPORT_DATE: 2024-01-15` in all `.txt` files under `/data/records/`.
2. Deduplicate the files by content: keep only one copy of each unique file (by SHA-256 hash of its content **after** the substitution). Remove the duplicate files, keeping the lexicographically first filename among duplicates.
3. Generate a checksum manifest at `/output/manifest.txt`. Each line must list the SHA-256 hash and filename (relative to `/data/records/`) of every surviving file, sorted alphabetically by filename, in the format: `<sha256hex>  <filename>`

Write the manifest to `/output/manifest.txt`.