```bash
#!/usr/bin/env bash
set -euo pipefail

MESSY=/workspace/messy
CLEAN=/workspace/clean
REF=/workspace/reference
REPORT=/workspace/report.txt

# ── Stage 1: Deduplicate by SHA-256 content hash ──────────────────────────────
# For each group of files with the same hash, keep shortest name (alpha tiebreak), remove rest
declare -A hash_to_keeper
declare -A hash_to_len

while IFS= read -r -d '' fpath; do
  fname=$(basename "$fpath")
  h=$(sha256sum "$fpath" | cut -d' ' -f1)
  flen=${#fname}
  if [[ -z "${hash_to_keeper[$h]:-}" ]]; then
    hash_to_keeper[$h]="$fname"
    hash_to_len[$h]=$flen
  else
    keeper="${hash_to_keeper[$h]}"
    klen=${hash_to_len[$h]}
    # prefer shorter name, then lexicographically smaller
    if [[ $flen -lt $klen ]] || [[ $flen -eq $klen && "$fname" < "$keeper" ]]; then
      # current file is better keeper, remove old keeper
      rm -f "$MESSY/$keeper"
      hash_to_keeper[$h]="$fname"
      hash_to_len[$h]=$flen
    else
      rm -f "$fpath"
    fi
  fi
done < <(find "$MESSY" -maxdepth 1 -name '*.rs' -print0 | sort -z)

# ── Stage 2: Bulk rename with pattern rules ────────────────────────────────────
clean_stem() {
  local stem="$1"
  # lowercase
  stem=$(echo "$stem" | tr '[:upper:]' '[:lower:]')
  # replace runs of non-alphanumeric with underscore
  stem=$(echo "$stem" | sed 's/[^a-z0-9]\+/_/g')
  # strip leading/trailing underscores
  stem=$(echo "$stem" | sed 's/^_\+//;s/_\+$//')
  # remove trailing _copy, _dup, _bak, _1, _2, _3 (repeat)
  local prev=''
  while [[ "$stem" != "$prev" ]]; do
    prev="$stem"
    stem=$(echo "$stem" | sed 's/_\(copy\|dup\|bak\|[123]\)$//')
  done
  echo "$stem"
}

declare -A cleaned_to_original
declare -A orig_to_cleaned

# First pass: determine mapping, detect conflicts
while IFS= read -r -d '' fpath; do
  fname=$(basename "$fpath")
  stem="${fname%.rs}"
  cs=$(clean_stem "$stem")
  cleaned="${cs}.rs"
  if [[ -z "${cleaned_to_original[$cleaned]:-}" ]]; then
    cleaned_to_original[$cleaned]="$fname"
    orig_to_cleaned[$fname]="$cleaned"
  else
    existing="${cleaned_to_original[$cleaned]}"
    # keep lexicographically first original
    if [[ "$fname" < "$existing" ]]; then
      # discard existing, keep current
      rm -f "$MESSY/$existing"
      cleaned_to_original[$cleaned]="$fname"
      orig_to_cleaned[$fname]="$cleaned"
      unset "orig_to_cleaned[$existing]" 2>/dev/null || true
    else
      rm -f "$fpath"
    fi
  fi
done < <(find "$MESSY" -maxdepth 1 -name '*.rs' -print0 | sort -z)

# Second pass: atomically rename
for orig in "${!orig_to_cleaned[@]}"; do
  cleaned="${orig_to_cleaned[$orig]}"
  if [[ "$orig" != "$cleaned" ]]; then
    if [[ -f "$MESSY/$orig" ]]; then
      cp "$MESSY/$orig" "$MESSY/${cleaned}.tmp"
      mv "$MESSY/${cleaned}.tmp" "$MESSY/$cleaned"
      rm -f "$MESSY/$orig"
    fi
  fi
done

# ── Stage 3: Compare against reference, copy matches ─────────────────────────
declare -A messy_files
while IFS= read -r -d '' fpath; do
  fname=$(basename "$fpath")
  messy_files[$fname]="$fpath"
done < <(find "$MESSY" -maxdepth 1 -name '*.rs' -print0)

report_lines=()
while IFS= read -r -d '' refpath; do
  rfname=$(basename "$refpath")
  refhash=$(sha256sum "$refpath" | cut -d' ' -f1)
  if [[ -n "${messy_files[$rfname]:-}" ]]; then
    mhash=$(sha256sum "${messy_files[$rfname]}" | cut -d' ' -f1)
    if [[ "$mhash" == "$refhash" ]]; then
      cp "${messy_files[$rfname]}" "$CLEAN/$rfname"
      report_lines+=("MATCH $rfname")
    else
      report_lines+=("MISMATCH_CONTENT $rfname")
    fi
  else
    report_lines+=("MISMATCH_NAME $rfname")
  fi
done < <(find "$REF" -maxdepth 1 -name '*.rs' -print0 | sort -z)

# Sort report lines by filename (second field)
printf '%s\n' "${report_lines[@]}" | sort -k2 > "$REPORT"

echo "Done. Report:"
cat "$REPORT"
```