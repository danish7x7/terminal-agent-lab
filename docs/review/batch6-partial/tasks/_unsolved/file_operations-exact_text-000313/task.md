# Release Archive Preparation

You are preparing a versioned release archive for a software project. The raw source tree lives at `/project/src`. Follow the steps below to produce a clean release package at `/output/release.tar.gz` and a manifest at `/output/manifest.txt`.

## Step 1 – Create a canonical staging area

Create the directory `/staging/release-1.0/`.

## Step 2 – Symlink resolution: populate staging from source

The source tree at `/project/src` contains regular files **and** symlinks. Walk the entire tree recursively. For every file (whether it is a symlink or a real file) copy the **resolved** (dereferenced) content into `/staging/release-1.0/` preserving the relative path. Do **not** include any dangling symlinks. Directories must be created as real directories (not symlinks).

## Step 3 – Strip large files

Delete every file under `/staging/release-1.0/` whose size **strictly exceeds 2048 bytes**.

## Step 4 – Strip old files

Delete every file under `/staging/release-1.0/` whose last-modification time is **older than 2024-01-01 00:00:00 UTC**. (Hint: the reference Unix timestamp for that moment is 1704067200.)

## Step 5 – Strip test artifacts

Delete every file under `/staging/release-1.0/` whose name matches the glob `*.tmp` or `*.log`.

## Step 6 – Build the release archive

Create `/output/release.tar.gz` as a gzip-compressed tar archive of `/staging/release-1.0/` such that paths inside the archive are relative (i.e. start with `release-1.0/...`).

## Step 7 – Extract and verify

Extract the archive into `/verify/` so that `/verify/release-1.0/` is produced.

## Step 8 – Write the manifest

Write `/output/manifest.txt`: a **sorted** list of the relative paths of every **regular file** inside `/verify/release-1.0/`, one path per line, relative to `/verify/release-1.0/` (no leading `./`), with a trailing newline after the last entry.

Example line format: `lib/utils.py`
