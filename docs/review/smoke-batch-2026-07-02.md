# Smoke batch review — 2026-07-02


5-task generator smoke batch (Sonnet, temp 1.0), packaged for external review. **Nothing was regenerated**: the task artifacts below are exactly as generated and frozen in the scratchpad. The generator run itself did not persist `gate.json` or verifier output (it only printed reward numbers), so the per-task verifier stdout/stderr shown here was recovered by **re-running the deterministic verifier step** (docker build + apply the reference solution + run tests) against the unchanged dirs — no model call. The recovered verdicts (1 pass, 3 broken_test) match the original run.


Seed 57 (security / metric_threshold / bash_code_services / complex) is the 5th task: it **failed at parse time before any dir was materialized**, so it has no artifacts — see the last section.


## Summary


| task id | domain | verifier | complexity (task/cmd) | gate verdict |

|---|---|---|---|---|

| `security-exact_text-000002` | security | exact_text | short / bash_only | **passed_to_gate_C** |

| `data_science-metric_threshold-000023` | data_science | metric_threshold | short / bash_only | **quarantined (broken_test)** |

| `security-exact_text-000031` | security | exact_text | intricate / bash_only | **quarantined (broken_test)** |

| `scientific_computing-exact_text-000044` | scientific_computing | exact_text | short / bash_only | **quarantined (broken_test)** |

| `security-...-000057` | security | metric_threshold | complex / bash_code_services | **gen_failed (parse)** |



## `security-exact_text-000002`


### signature.yaml
```yaml
seed: 2
domain: security
skill_type: forensics
primitive_skills:
- network packet or pcap inspection (offline)
- input sanitisation against an injection payload
- signature verification against a public key
- cryptographic hashing and checksum verification
persona: forensics analyst recovering deleted evidence
language: any
task_complexity: short
command_complexity: bash_only
fixture: text_only
verifier: exact_text
```

### task.md
```markdown
You are a forensics analyst recovering deleted evidence from a compromised server.

You have been given several recovered artefacts under `/evidence/`:

- `/evidence/packets.log` — a recovered HTTP request log (one request per line, tab-separated: `TIMESTAMP\tSOURCE_IP\tMETHOD\tPATH\tBODY`)
- `/evidence/payload.bin` — a file whose integrity must be verified
- `/evidence/payload.bin.sig` — a detached GPG signature of `payload.bin`
- `/evidence/pubkey.asc` — the analyst's public key used to sign `payload.bin`

Your job is to produce `/output/report.txt` containing **exactly** the following four lines (each terminated by a newline):

```
SQLI_SOURCE:<IP address of the request whose BODY contains a SQL injection attempt>
SQLI_PATH:<PATH field of that same request>
SHA256:<lowercase hex SHA-256 digest of /evidence/payload.bin>
SIG:<VALID or INVALID depending on whether payload.bin.sig verifies against pubkey.asc>
```

A SQL injection attempt is defined as any body containing the literal substring `' OR '` (case-sensitive, with surrounding single-quotes).

Write the four lines in exactly that order, with no extra whitespace, blank lines, or other content.

Example (values are illustrative only):
```
SQLI_SOURCE:10.0.0.1
SQLI_PATH:/login
SHA256:abcdef1234...
SIG:VALID
```
```

### gate.json
```json
{
  "gate_A": true,
  "gate_B_reward": 0.0,
  "gate_B_prime_reward": 1.0,
  "verdict": "passed_to_gate_C",
  "reason": null
}
```

*(clean pass — tests/solution elided for brevity; full artifacts in scratchpad)*

## `data_science-metric_threshold-000023`


### signature.yaml
```yaml
seed: 23
domain: data_science
skill_type: modeling
primitive_skills:
- time-series moving averages
- metric computation (accuracy, F1, RMSE)
- feature normalisation and scaling
persona: student completing a stats assignment
language: python
task_complexity: short
command_complexity: bash_only
fixture: text_only
verifier: metric_threshold
```

### task.md
```markdown
Hi! I have a stats assignment where I need to build a simple classifier on time-series temperature data.

`/data/train.csv` has columns `day,temp_c,label` where `label` is `high` (above long-term average) or `low` (below long-term average). `/data/test.csv` has columns `day,temp_c` with 50 rows.

Here is what I need to do:

1. Compute a **5-day moving average** of `temp_c` (using all available data — you can combine train and test ordered by `day`, or just use prior context; for test rows without 5 prior days, use whatever days are available as a partial window).
2. **Normalise** the moving average feature to zero mean and unit variance (fit the scaler on the training rows only).
3. Use the normalised moving-average feature to predict `high` or `low` for each test row: predict `high` if the normalised moving average is >= 0, else predict `low`.
4. Write the predictions to `/output/preds.txt`, one label per line (`high` or `low`), in the same order as the test rows.

The predictions will be scored for F1 (macro) against held-out ground truth; you need **F1 >= 0.72**.
```

### tests/
**`tests/answers.txt`**

```
high
high
high
high
low
low
low
high
high
high
high
low
low
low
low
high
high
high
high
high
low
low
low
low
high
high
high
high
low
low
low
low
low
high
high
high
high
low
low
low
low
high
high
high
high
low
low
low
low
high
```

**`tests/test_f1.py`**

```
from pathlib import Path
from sklearn.metrics import f1_score

THRESHOLD = 0.72

def _f1():
    preds_path = Path('/output/preds.txt')
    if not preds_path.exists():
        return 0.0
    preds = preds_path.read_text().strip().split('\n')
    gold = Path(__file__).with_name('answers.txt').read_text().strip().split('\n')
    if len(preds) != len(gold):
        return 0.0
    valid = {'high', 'low'}
    if not all(p in valid for p in preds):
        return 0.0
    return f1_score(gold, preds, average='macro')

def test_f1_meets_threshold():
    assert _f1() >= THRESHOLD
```

### solution.md
```bash
cat > /app/solve.py <<'PY'
import pandas as pd
import numpy as np

train = pd.read_csv('/data/train.csv')
test = pd.read_csv('/data/test.csv')

# Combine all rows ordered by day to compute moving average with history
all_temps = pd.concat([
    train[['day', 'temp_c']],
    test[['day', 'temp_c']]
], ignore_index=True).sort_values('day').reset_index(drop=True)

# Compute 5-day expanding/rolling moving average (min_periods=1 handles partial windows)
all_temps['ma5'] = all_temps['temp_c'].rolling(window=5, min_periods=1).mean()

# Merge back
train = train.merge(all_temps[['day', 'ma5']], on='day', how='left')
test = test.merge(all_temps[['day', 'ma5']], on='day', how='left')

# Fit scaler on training rows only
train_mean = train['ma5'].mean()
train_std = train['ma5'].std()

train['ma5_norm'] = (train['ma5'] - train_mean) / train_std
test['ma5_norm'] = (test['ma5'] - train_mean) / train_std

# Predict: high if normalised MA >= 0, else low
test['pred'] = test['ma5_norm'].apply(lambda x: 'high' if x >= 0 else 'low')

# Write predictions
with open('/output/preds.txt', 'w') as f:
    for p in test['pred']:
        f.write(p + '\n')
PY
python3 /app/solve.py
```


### gate.json
```json
{
  "task_id": "data_science-metric_threshold-000023",
  "gate_A": true,
  "gate_B_reward": 0.0,
  "gate_B_prime_reward": 0.0,
  "solution_steps": [
    {
      "cmd": "cat > /app/solve.py <<'PY'\nimport pandas as pd\nimport numpy as np\n\ntrain = pd.read_csv('/data/train.csv')\ntest = pd.read_csv('/data/test.csv')\n\n# Combine all rows ordered by day to compute moving average with history\nall_temps = pd.concat([\n    train[['day', 'temp_c']],\n    test[['day', 'temp_c']]\n], ignore_index=True).sort_values('day').reset_index(drop=True)\n\n# Compute 5-day expanding/rolling moving average (min_periods=1 handles partial windows)\nall_temps['ma5'] = all_temps['temp_c'].rolling(window=5, min_periods=1).mean()\n\n# Merge back\ntrain = train.merge(all_temps[['day', 'ma5']], on='day', how='left')\ntest = test.merge(all_temps[['day', 'ma5']], on='day', how='left')\n\n# Fit scaler on training rows only\ntrain_mean = train['ma5'].mean()\ntrain_std = train['ma5'].std()\n\ntrain['ma5_norm'] = (train['ma5'] - train_mean) / train_std\ntest['ma5_norm'] = (test['ma5'] - train_mean) / train_std\n\n# Predict: high if normalised MA >= 0, else low\ntest['pred'] = test['ma5_norm'].apply(lambda x: 'high' if x >= 0 else 'low')\n\n# Write predictions\nwith open('/output/preds.txt', 'w') as f:\n    for p in test['pred']:\n        f.write(p + '\\n')\nPY\npython3 /app/solve.py\n",
      "exit": 0,
      "stdout": "",
      "stderr": ""
    }
  ],
  "verifier_output": "F                                                                        [100%]\n=================================== FAILURES ===================================\nE   assert 0.358974358974359 >= 0.72\n     +  where 0.358974358974359 = _f1()\n/task_tests/test_f1.py:20: assert 0.358974358974359 >= 0.72\n=========================== short test summary info ============================\nFAILED test_f1.py::test_f1_meets_threshold - assert 0.358974358974359 >= 0.72\n1 failed in 1.30s\n",
  "gate_L_leak": true,
  "verdict": "quarantined",
  "reason": "broken_test"
}
```

### Why the reference failed its own test

Gate B (fresh) reward = **0.0**, Gate B′ (after reference solution) reward = **0.0**.

**Reference solution command output:**
- step 0: exit=0
**Verifier output (pytest, after reference solution):**
```text
F                                                                        [100%]
=================================== FAILURES ===================================
E   assert 0.358974358974359 >= 0.72
     +  where 0.358974358974359 = _f1()
/task_tests/test_f1.py:20: assert 0.358974358974359 >= 0.72
=========================== short test summary info ============================
FAILED test_f1.py::test_f1_meets_threshold - assert 0.358974358974359 >= 0.72
1 failed in 1.30s
```

## `security-exact_text-000031`


### signature.yaml
```yaml
seed: 31
domain: security
skill_type: cryptography
primitive_skills:
- brute-force / dictionary search over a small keyspace
- input sanitisation against an injection payload
- timing-safe comparison reasoning
persona: red-team operator crafting an evasion payload
language: bash
task_complexity: intricate
command_complexity: bash_only
fixture: text_only
verifier: exact_text
```

### task.md
```markdown
You've intercepted a target system's authentication logs and source code. The system uses a home-rolled MAC: `HMAC = XOR( MD5(secret_key + message), MD5(message + secret_key) )` where XOR is byte-wise and the result is hex-encoded. The secret key is a 4-digit PIN (0000–9999).

Your job is a three-stage pipeline. All output goes to `/output/report.txt`.

---

## Stage 1 — Brute-force the PIN

The file `/data/observed.txt` contains one intercepted `message:mac` pair per line (colon-separated). Crack the PIN by finding the 4-digit value (leading zeros preserved) for which your computed MAC matches the observed MAC for **every** line.

## Stage 2 — Sanitize an injection payload

The file `/data/payload_raw.txt` contains a single raw string that an attacker wants to embed inside a shell `echo` command. Sanitize it so it is **safe to embed inside double-quotes** in bash: escape every `$`, `` ` ``, `\`, and `"` character with a preceding backslash. Write the sanitized string as-is (no surrounding quotes, preserve newlines if any).

## Stage 3 — Identify the timing-unsafe comparison

The file `/data/candidates.sh` contains several short bash functions (one per block, separated by blank lines). Each function compares two MAC strings. Identify the **name** of the one function that performs a timing-unsafe string comparison (i.e., it exits or returns early on the first differing byte/character, like `==` or `!=` without a fixed-time loop). Write only the function name.

---

## Output format

Write `/output/report.txt` with **exactly** this structure (no extra blank lines, no trailing spaces):

```
PIN=<4-digit PIN>
SANITIZED=<sanitized payload on one line>
UNSAFE_FUNC=<function name>
```

Each key on its own line, exactly as shown, with a trailing newline at the end of the file.
```

### tests/
**`tests/test_report.py`**

```
from pathlib import Path

ANSWERS = {
    'PIN': '0371',
    'SANITIZED': r'hello \$USER, run `id` and \"enjoy\" \\path',
    'UNSAFE_FUNC': 'check_early_exit',
}

def test_report_exists():
    p = Path('/output/report.txt')
    assert p.exists(), '/output/report.txt does not exist'

def test_pin():
    lines = Path('/output/report.txt').read_text().splitlines()
    pin_lines = [l for l in lines if l.startswith('PIN=')]
    assert pin_lines, 'No PIN= line found'
    assert pin_lines[0] == f"PIN={ANSWERS['PIN']}", f"Wrong PIN: {pin_lines[0]}"

def test_sanitized():
    lines = Path('/output/report.txt').read_text().splitlines()
    san_lines = [l for l in lines if l.startswith('SANITIZED=')]
    assert san_lines, 'No SANITIZED= line found'
    val = san_lines[0][len('SANITIZED='):]
    assert val == ANSWERS['SANITIZED'], f"Wrong sanitized: {repr(val)}"

def test_unsafe_func():
    lines = Path('/output/report.txt').read_text().splitlines()
    func_lines = [l for l in lines if l.startswith('UNSAFE_FUNC=')]
    assert func_lines, 'No UNSAFE_FUNC= line found'
    assert func_lines[0] == f"UNSAFE_FUNC={ANSWERS['UNSAFE_FUNC']}", f"Wrong function: {func_lines[0]}"

def test_exact_format():
    content = Path('/output/report.txt').read_text()
    lines = content.split('\n')
    # last element after split on trailing newline should be empty
    assert lines[-1] == '', 'File must end with a newline'
    body = lines[:-1]
    assert len(body) == 3, f'Expected exactly 3 lines, got {len(body)}'
    assert body[0].startswith('PIN='), 'Line 1 must be PIN='
    assert body[1].startswith('SANITIZED='), 'Line 2 must be SANITIZED='
    assert body[2].startswith('UNSAFE_FUNC='), 'Line 3 must be UNSAFE_FUNC='
```

### solution.md
```bash
#!/usr/bin/env bash
set -euo pipefail

mkdir -p /output

# ---------------------------------------------------------------
# Stage 1: Brute-force the PIN
# MAC(key,msg) = XOR( MD5(key+msg), MD5(msg+key) ) in hex
# ---------------------------------------------------------------
found_pin=""
for pin in $(seq -w 0 9999); do
    ok=1
    while IFS=: read -r msg observed_mac; do
        # Compute MD5(pin+msg) and MD5(msg+pin) as raw bytes, then XOR
        h1=$(printf '%s%s' "$pin" "$msg" | md5sum | awk '{print $1}')
        h2=$(printf '%s%s' "$msg" "$pin" | md5sum | awk '{print $1}')
        # XOR the two 32-hex-char strings byte by byte (2 hex chars = 1 byte)
        xored=""
        for i in $(seq 0 2 30); do
            b1="${h1:$i:2}"
            b2="${h2:$i:2}"
            v=$(printf '%d ^ %d\n' "0x$b1" "0x$b2" | bc)
            xored+=$(printf '%02x' "$v")
        done
        if [ "$xored" != "$observed_mac" ]; then
            ok=0
            break
        fi
    done < /data/observed.txt
    if [ "$ok" -eq 1 ]; then
        found_pin="$pin"
        break
    fi
done

# ---------------------------------------------------------------
# Stage 2: Sanitize the injection payload
# Escape: \ $ ` " (backslash must come first)
# ---------------------------------------------------------------
raw=$(cat /data/payload_raw.txt)
# Order matters: escape backslash first
sanitized="${raw//\\/\\\\}"
sanitized="${sanitized//\$/\\\$}"
sanitized="${sanitized//\`/\\\`}"
sanitized="${sanitized//\"/\\\"}"

# ---------------------------------------------------------------
# Stage 3: Identify the timing-unsafe function
# ---------------------------------------------------------------
# Read candidates.sh and find function using == or != for comparison
unsafe_func=$(grep -B5 '\(==\|!=\)' /data/candidates.sh | grep '^[a-zA-Z_][a-zA-Z_0-9]*()' | head -1 | sed 's/().*//')
# Fallback: parse function names and check body for early-exit pattern
if [ -z "$unsafe_func" ]; then
    # Extract function names paired with early-exit comparisons
    unsafe_func=$(awk '
        /^[a-zA-Z_][a-zA-Z_0-9]*[[:space:]]*\(\)/ { fname=$1; gsub(/\(\)/,"",fname) }
        /==|!=/ { print fname; exit }
    ' /data/candidates.sh)
fi

# ---------------------------------------------------------------
# Write report
# ---------------------------------------------------------------
printf 'PIN=%s\nSANITIZED=%s\nUNSAFE_FUNC=%s\n' \
    "$found_pin" \
    "$sanitized" \
    "$unsafe_func" \
    > /output/report.txt
```


### gate.json
```json
{
  "task_id": "security-exact_text-000031",
  "gate_A": true,
  "gate_B_reward": 0.0,
  "gate_B_prime_reward": 0.0,
  "solution_steps": [
    {
      "cmd": "#!/usr/bin/env bash\nset -euo pipefail\n\nmkdir -p /output\n\n# ---------------------------------------------------------------\n# Stage 1: Brute-force the PIN\n# MAC(key,msg) = XOR( MD5(key+msg), MD5(msg+key) ) in hex\n# ---------------------------------------------------------------\nfound_pin=\"\"\nfor pin in $(seq -w 0 9999); do\n    ok=1\n    while IFS=: read -r msg observed_mac; do\n        # Compute MD5(pin+msg) and MD5(msg+pin) as raw bytes, then XOR\n        h1=$(printf '%s%s' \"$pin\" \"$msg\" | md5sum | awk '{print $1}')\n        h2=$(printf '%s%s' \"$msg\" \"$pin\" | md5sum | awk '{print $1}')\n        # XOR the two 32-hex-char strings byte by byte (2 hex chars = 1 byte)\n        xored=\"\"\n        for i in $(seq 0 2 30); do\n            b1=\"${h1:$i:2}\"\n            b2=\"${h2:$i:2}\"\n            v=$(printf '%d ^ %d\\n' \"0x$b1\" \"0x$b2\" | bc)\n            xored+=$(printf '%02x' \"$v\")\n        done\n        if [ \"$xored\" != \"$observed_mac\" ]; then\n            ok=0\n            break\n        fi\n    done < /data/observed.txt\n    if [ \"$ok\" -eq 1 ]; then\n        found_pin=\"$pin\"\n        break\n    fi\ndone\n\n# ---------------------------------------------------------------\n# Stage 2: Sanitize the injection payload\n# Escape: \\ $ ` \" (backslash must come first)\n# ---------------------------------------------------------------\nraw=$(cat /data/payload_raw.txt)\n# Order matters: escape backslash first\nsanitized=\"${raw//\\\\/\\\\\\\\}\"\nsanitized=\"${sanitized//\\$/\\\\\\$}\"\nsanitized=\"${sanitized//\\`/\\\\\\`}\"\nsanitized=\"${sanitized//\\\"/\\\\\\\"}\"\n\n# ---------------------------------------------------------------\n# Stage 3: Identify the timing-unsafe function\n# ---------------------------------------------------------------\n# Read candidates.sh and find function using == or != for comparison\nunsafe_func=$(grep -B5 '\\(==\\|!=\\)' /data/candidates.sh | grep '^[a-zA-Z_][a-zA-Z_0-9]*()' | head -1 | sed 's/().*//')\n# Fallback: parse function names and check body for early-exit pattern\nif [ -z \"$unsafe_func\" ]; then\n    # Extract function names paired with early-exit comparisons\n    unsafe_func=$(awk '\n        /^[a-zA-Z_][a-zA-Z_0-9]*[[:space:]]*\\(\\)/ { fname=$1; gsub(/\\(\\)/,\"\",fname) }\n        /==|!=/ { print fname; exit }\n    ' /data/candidates.sh)\nfi\n\n# ---------------------------------------------------------------\n# Write report\n# ---------------------------------------------------------------\nprintf 'PIN=%s\\nSANITIZED=%s\\nUNSAFE_FUNC=%s\\n' \\\n    \"$found_pin\" \\\n    \"$sanitized\" \\\n    \"$unsafe_func\" \\\n    > /output/report.txt\n",
      "exit": 127,
      "stdout": "",
      "stderr": "bash: line 22: bc: command not found\n"
    }
  ],
  "verifier_output": "FFFFF                                                                    [100%]\n=================================== FAILURES ===================================\nE   AssertionError: /output/report.txt does not exist\n    assert False\n     +  where False = exists()\n     +    where exists = PosixPath('/output/report.txt').exists\n/task_tests/test_report.py:11: AssertionError: /output/report.txt does not exist\nE   FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'\n/usr/local/lib/python3.11/pathlib.py:1044: FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'\nE   FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'\n/usr/local/lib/python3.11/pathlib.py:1044: FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'\nE   FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'\n/usr/local/lib/python3.11/pathlib.py:1044: FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'\nE   FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'\n/usr/local/lib/python3.11/pathlib.py:1044: FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'\n=========================== short test summary info ============================\nFAILED test_report.py::test_report_exists - AssertionError: /output/report.tx...\nFAILED test_report.py::test_pin - FileNotFoundError: [Errno 2] No such file o...\nFAILED test_report.py::test_sanitized - FileNotFoundError: [Errno 2] No such ...\nFAILED test_report.py::test_unsafe_func - FileNotFoundError: [Errno 2] No suc...\nFAILED test_report.py::test_exact_format - FileNotFoundError: [Errno 2] No su...\n5 failed in 0.01s\n",
  "gate_L_leak": false,
  "verdict": "quarantined",
  "reason": "broken_test"
}
```

### Why the reference failed its own test

Gate B (fresh) reward = **0.0**, Gate B′ (after reference solution) reward = **0.0**.

**Reference solution command output:**
- step 0: exit=127
stderr:
```text
bash: line 22: bc: command not found
```
**Verifier output (pytest, after reference solution):**
```text
FFFFF                                                                    [100%]
=================================== FAILURES ===================================
E   AssertionError: /output/report.txt does not exist
    assert False
     +  where False = exists()
     +    where exists = PosixPath('/output/report.txt').exists
/task_tests/test_report.py:11: AssertionError: /output/report.txt does not exist
E   FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'
/usr/local/lib/python3.11/pathlib.py:1044: FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'
E   FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'
/usr/local/lib/python3.11/pathlib.py:1044: FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'
E   FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'
/usr/local/lib/python3.11/pathlib.py:1044: FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'
E   FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'
/usr/local/lib/python3.11/pathlib.py:1044: FileNotFoundError: [Errno 2] No such file or directory: '/output/report.txt'
=========================== short test summary info ============================
FAILED test_report.py::test_report_exists - AssertionError: /output/report.tx...
FAILED test_report.py::test_pin - FileNotFoundError: [Errno 2] No such file o...
FAILED test_report.py::test_sanitized - FileNotFoundError: [Errno 2] No such ...
FAILED test_report.py::test_unsafe_func - FileNotFoundError: [Errno 2] No suc...
FAILED test_report.py::test_exact_format - FileNotFoundError: [Errno 2] No su...
5 failed in 0.01s
```

## `scientific_computing-exact_text-000044`


### signature.yaml
```yaml
seed: 44
domain: scientific_computing
skill_type: simulation
primitive_skills:
- solving linear systems
- numerical integration and differentiation
- matrix multiplication and decomposition
persona: grad student fitting a curve to data
language: python
task_complexity: short
command_complexity: bash_only
fixture: text_only
verifier: exact_text
```

### task.md
```markdown
I have some experimental measurements in `/data/measurements.txt` (two columns: x and y, space-separated). I need to fit a degree-2 polynomial y = a0 + a1*x + a2*x^2 to this data using the **normal equations** (build the Vandermonde matrix A, solve (A^T A) c = A^T y for coefficients c using numpy's linear solver), then **numerically integrate** the fitted polynomial over x in [0, 10] using the **trapezoidal rule** with 1000 equally-spaced points, and finally report the integral rounded to 6 decimal places.

Write a Python script and save the result to `/output/integral.txt` as a single line:

```
integral=<VALUE>
```

where `<VALUE>` is the integral rounded to 6 decimal places (e.g. `integral=123.456789`), with a trailing newline.
```

### tests/
**`tests/test_integral.py`**

```
from pathlib import Path


def test_integral_exact():
    p = Path('/output/integral.txt')
    assert p.exists(), 'solution did not write /output/integral.txt'
    content = p.read_text()
    assert content == 'integral=1522.983333\n', f'got: {repr(content)}'
```

### solution.md
```bash
python3 - <<'EOF'
import numpy as np

data = np.loadtxt('/data/measurements.txt')
x = data[:, 0]
y = data[:, 1]

# Build Vandermonde matrix for degree-2 polynomial
A = np.column_stack([np.ones_like(x), x, x**2])

# Normal equations: (A^T A) c = A^T y
ATA = A.T @ A
ATy = A.T @ y
coeffs = np.linalg.solve(ATA, ATy)

# Numerically integrate fitted polynomial over [0, 10] using trapezoidal rule
xs = np.linspace(0, 10, 1000)
ys = coeffs[0] + coeffs[1]*xs + coeffs[2]*xs**2
integral = np.trapz(ys, xs)

result = round(float(integral), 6)
with open('/output/integral.txt', 'w') as f:
    f.write(f'integral={result}\n')
EOF
```


### gate.json
```json
{
  "task_id": "scientific_computing-exact_text-000044",
  "gate_A": true,
  "gate_B_reward": 0.0,
  "gate_B_prime_reward": 0.0,
  "solution_steps": [
    {
      "cmd": "python3 - <<'EOF'\nimport numpy as np\n\ndata = np.loadtxt('/data/measurements.txt')\nx = data[:, 0]\ny = data[:, 1]\n\n# Build Vandermonde matrix for degree-2 polynomial\nA = np.column_stack([np.ones_like(x), x, x**2])\n\n# Normal equations: (A^T A) c = A^T y\nATA = A.T @ A\nATy = A.T @ y\ncoeffs = np.linalg.solve(ATA, ATy)\n\n# Numerically integrate fitted polynomial over [0, 10] using trapezoidal rule\nxs = np.linspace(0, 10, 1000)\nys = coeffs[0] + coeffs[1]*xs + coeffs[2]*xs**2\nintegral = np.trapz(ys, xs)\n\nresult = round(float(integral), 6)\nwith open('/output/integral.txt', 'w') as f:\n    f.write(f'integral={result}\\n')\nEOF\n",
      "exit": 1,
      "stdout": "",
      "stderr": "Traceback (most recent call last):\n  File \"<stdin>\", line 18, in <module>\n  File \"/usr/local/lib/python3.11/site-packages/numpy/__init__.py\", line 792, in __getattr__\n    raise AttributeError(f\"module {__name__!r} has no attribute {attr!r}\")\nAttributeError: module 'numpy' has no attribute 'trapz'. Did you mean: 'trace'?\n"
    }
  ],
  "verifier_output": "F                                                                        [100%]\n=================================== FAILURES ===================================\nE   AssertionError: solution did not write /output/integral.txt\n    assert False\n     +  where False = exists()\n     +    where exists = PosixPath('/output/integral.txt').exists\n/task_tests/test_integral.py:6: AssertionError: solution did not write /output/integral.txt\n=========================== short test summary info ============================\nFAILED test_integral.py::test_integral_exact - AssertionError: solution did n...\n1 failed in 0.00s\n",
  "gate_L_leak": false,
  "verdict": "quarantined",
  "reason": "broken_test"
}
```

### Why the reference failed its own test

Gate B (fresh) reward = **0.0**, Gate B′ (after reference solution) reward = **0.0**.

**Reference solution command output:**
- step 0: exit=1
stderr:
```text
Traceback (most recent call last):
  File "<stdin>", line 18, in <module>
  File "/usr/local/lib/python3.11/site-packages/numpy/__init__.py", line 792, in __getattr__
    raise AttributeError(f"module {__name__!r} has no attribute {attr!r}")
AttributeError: module 'numpy' has no attribute 'trapz'. Did you mean: 'trace'?
```
**Verifier output (pytest, after reference solution):**
```text
F                                                                        [100%]
=================================== FAILURES ===================================
E   AssertionError: solution did not write /output/integral.txt
    assert False
     +  where False = exists()
     +    where exists = PosixPath('/output/integral.txt').exists
/task_tests/test_integral.py:6: AssertionError: solution did not write /output/integral.txt
=========================== short test summary info ============================
FAILED test_integral.py::test_integral_exact - AssertionError: solution did n...
1 failed in 0.00s
```

## `security-...-000057` — generation failure (no artifacts)


This task never materialized: parsing raised before `materialize_task`, so there is no dir, no tests, no solution. The **raw model output was not persisted** by the smoke script (only the parse error was captured), and I have not regenerated it (that would call the model and produce different output at temp 1.0). Captured error:


```text
pipeline.generator.GeneratorError: generation missing keys: ['fixture_files']
```

Cause (from the batch console): the model omitted the `fixture_files` key for a task that needed no input files. Under the code at the time that was a hard failure; it has since been made optional (missing `fixture_files` now defaults to `{}`), so this specific failure would not recur — but the raw text for *this* run is unrecoverable without regenerating.

