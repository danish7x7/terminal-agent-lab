You are a student implementing a version-upgrade pipeline for C source files.

The system works as follows:

1. **Mock API** — `/api/responses/` contains JSON files that simulate responses from a "package registry" API. Each file is named `<package>.json` and contains version and patch information.

2. **Your job** — Write a bash script `/solution/upgrade.sh` that, for each package listed in `/data/packages.txt`:
   a. Reads the corresponding JSON file from `/api/responses/<package>.json` to extract `latest_version` and `patch` fields.
   b. Compares the `latest_version` from the API response with the `current_version` listed in `/data/packages.txt` using **semantic versioning** (MAJOR.MINOR.PATCH). If the latest version is strictly greater than the current version, proceed; otherwise skip.
   c. Applies the patch (a unified diff stored as a string in the `patch` field of the JSON) to the corresponding C source file in `/src/<package>.c`, writing the patched result to `/output/<package>.c`.
   d. If the version is NOT newer (already up-to-date or downgrade), copy the original file unchanged to `/output/<package>.c`.

**Input files:**

- `/data/packages.txt` — lines of format `<package> <current_version>`
- `/api/responses/<package>.json` — JSON with fields:
  - `latest_version`: a semver string like `"2.1.0"`
  - `patch`: a unified diff string (newlines encoded as `\n` inside the JSON string)
- `/src/<package>.c` — C source files to potentially patch

**Output:** For each package in `/data/packages.txt`, write `/output/<package>.c`.

**Semver comparison rule:** version A is greater than B if, comparing MAJOR then MINOR then PATCH as integers, A is lexicographically later. E.g., `1.10.0 > 1.9.0`, `2.0.0 > 1.99.99`.

**Patch application:** The `patch` field in the JSON is a unified diff. Extract it (interpreting `\n` escape sequences) and apply it with the `patch` command.

Run your script: `bash /solution/upgrade.sh`

The output files must end up in `/output/`.