# Recovering a Mis-Named Batch of Rust Source Files

I accidentally ran a broken batch-rename script on my Rust project directory and now everything is a mess. I need your help cleaning it up.

## The Situation

The directory `/workspace/messy/` contains a jumble of `.rs` files with broken names, duplicates (same content, different names), and some files that were renamed with a wrong prefix/suffix pattern.

The **original correct files** should have names matching this pattern:
- Lowercase letters, digits, and underscores only
- End in `.rs`
- No numeric suffix like `_1`, `_2`, `_copy`, `_dup`, `_bak` appended
- No leading/trailing underscores in the stem

The **target directory** is `/workspace/clean/`.

## What You Must Do (in order)

### Stage 1 — Deduplicate by content hash
Within `/workspace/messy/`, find all files that have identical content (by SHA-256). Keep only ONE representative per group of duplicates (prefer the shortest filename; break ties alphabetically). Remove the other duplicates **in place** using safe atomic replacement (write a temp file, then `mv` it over the original, or use `mv` to swap — never leave a file half-written). Actually, for removals, just `rm` the duplicates, but for any file you modify or create, write to a `.tmp` file first then atomically rename it.

### Stage 2 — Bulk rename with pattern rules
After deduplication, rename every surviving file so its stem conforms to the clean naming rules:
1. Convert the stem to lowercase.
2. Replace any run of non-alphanumeric characters (anything not `a-z`, `0-9`) with a single underscore.
3. Strip leading and trailing underscores from the stem.
4. Remove any trailing `_copy`, `_dup`, `_bak`, `_1`, `_2`, `_3` suffixes (repeat until none remain).
5. The final filename is `<cleaned_stem>.rs`.

If two files would map to the same cleaned name after these rules, keep only the one that is **lexicographically first** among the originals and discard the other.

Perform all renames atomically (write content to a `.tmp` file in `/workspace/messy/`, then `mv` into place).

### Stage 3 — Compare and copy to clean directory
Compare the cleaned `/workspace/messy/` tree against `/workspace/reference/` (which I am providing as the ground truth of what the directory SHOULD look like after cleaning). 

For every file in `/workspace/messy/` whose name AND content **both match** a file in `/workspace/reference/`, copy it into `/workspace/clean/` (maintaining flat structure — no subdirectories).

Write a report to `/workspace/report.txt` with lines in the format:
```
MATCH <filename>
MISMATCH_NAME <filename>
MISMATCH_CONTENT <filename>
```
- `MATCH` — file exists in messy with correct name and correct content
- `MISMATCH_CONTENT` — file exists in messy with correct name but wrong content
- `MISMATCH_NAME` — file exists in reference but no file with that name exists in messy

Lines must be sorted alphabetically by filename.

### Output
- `/workspace/clean/` — contains all matched files
- `/workspace/report.txt` — the comparison report

**Success metric:** at least 0.55 of the reference files must appear as `MATCH` in your report (i.e., correctly recovered and placed in `/workspace/clean/`).