# 003 — Phase 2 pipeline design

Status: accepted. Deviates from / builds on: [[001-scope]], [[data-pipeline]],
[[verifiers]], [[harness]].

**This note is authoritative** for the Phase 2 pipeline. It supersedes the
proposal that lived in the plan file: where they differ (the validation gate),
this note wins. It folds in five amendments to the gate and records the seven
places the paper under-specifies.

## Scope recap

~100 generated tasks (not 14.6k), `fixture = text_only` only, verifier kinds
`{exact_text, metric_threshold}` only (PROJECT_SPEC Phase 2; [[001-scope]]
Deviation 2). Everything below is sized to *measure* difficulty and diversity,
not to train on.

## 1. `axes.yaml` schema

One file, three axis shapes. The sampler resolves axes in listed order, so
domain-conditioned axes are drawn after `domain`.

- **flat categorical** — `values: [...]`, sampled uniformly. Used by `domain`
  (9), `task_complexity` (4), `command_complexity` (3), `fixture` (1 at our
  scope), `verifier` (2 at our scope). Complexity axes also carry a
  `descriptions:` map rendered verbatim into the generator prompt.
- **weighted categorical** — `weighted: {value: weight}`, normalized then
  sampled. Used by `language` (8 values, python/bash-biased).
- **domain-conditioned** — `per_domain: {domain: [...]}`, indexed by the drawn
  domain. Used by `skill_type` (4–7/domain), `primitive_skills`
  (author ~15/domain, `sample: {min: 3, max: 5}` without replacement), and
  `persona` (~6/domain).

Axis cardinalities and the first three axes' provenance follow paper Table 8
(domain/skill_type/primitive_skills seeded from Pi et al. 2026; the other six
are the paper's contribution).

**Task signature** = the dict of drawn values plus the RNG seed:
`{seed, domain, skill_type, primitive_skills[], persona, language,
task_complexity, command_complexity, fixture, verifier}`. Written to each task
dir as `signature.yaml` for reproducibility and for the later balance-score
plot (Eq. 1, [[evaluation]]).

**Sampler contract**: seeded `random.Random(seed)`; flat → uniform; weighted →
normalized; per_domain → indexed by domain; `sample:{min,max}` → draw a count,
then sample that many without replacement. Deterministic given the seed.

## 2. Validation gate (authoritative — amendments 1–5 folded in)

Our stand-in for the RL soft-filter the paper gets for free ([[001-scope]]
Deviation 3): the paper drops all-zero-reward groups from the gradient; we have
no gradient, so unsolvable/broken tasks must be caught explicitly or they
silently deflate pass@k. Five gates, cheap → expensive, run per task. Every
task gets a `gate.json`; nothing is ever silently deleted.

**Pass threshold** (single definition, referenced by all gates below): a
verifier run *passes* when its reward reaches the task's pass threshold —
`exact_text` → `1.0`; `metric_threshold` → the task's own `threshold` value
(`metric ≥ threshold`). "Below threshold" / "at threshold" everywhere below
mean relative to this per-kind value; no gate restates it.

Order: **A → B → B′ → L → C**. B′ runs *before* C so that a test which rejects
even a correct solution is blamed on the test, not on the agent. L (answer-leak)
runs after B′ (the reference answer is known to be well-formed by then) and
before the expensive C. Implemented in `pipeline/gate.py:run_gate`; every task
is moved to its bucket (`tasks/`, `tasks/_quarantine/`, `tasks/_unsolved/`) with
a durable `gate.json`. B, B′, and C all launch containers via the shared
`RunConfig.container()` so gate and eval flags never drift (amendment 5).

**Gate L — answer-leak (amend 6).** The reward-hacking exposure found while
authoring the `metric_threshold` exemplar — an answer key visible to the agent
lets it copy the answer instead of solving — is not specific to that task. It
is a hazard for **every reference-comparing verifier** (exact_text's expected
string, metric_threshold's held-out labels, any future oracle output). So it
must be an **automated invariant, not an authoring habit**. Gate L greps the
built image's filesystem *and* `task.md` for the reference answer / expected
output that the verifier checks against; if the answer is reachable from either
(the running container the agent sees, or the instructions), the task is
quarantined `answer_leak`. This is what enforces the design rule that the
ground truth lives only in `tests/` (copied in by `verifier.py` at verify time,
never in the image) — the exemplars follow it by construction, but Gate L makes
it structural for *generated* tasks where we can't trust authoring discipline.
Implementation note: extract the comparison target(s) from the verifier
(reference file(s) under `tests/`) and `grep -rF` each against the image
(`docker run ... find / -type f -exec grep`) and against `task.md`; small
literal answers are the common case, so fixed-string search suffices to start.
⚠️ Known limitation: catches *verbatim* leaks, not transformed ones (answer
base64-encoded in the image, or derivable rather than copied) — those still
rely on Gate B (an agent that reconstructs the answer without doing the task
would also pre-solve). Documented so the gate isn't mistaken for a proof.

⚠️ Needle source (learned the hard way): Gate L needles come from **reference
data files only** (`answers.txt` etc.), never from test `.py` source. Early
versions extracted string literals from the test code too, which flagged
*output-format tokens the task legitimately states in task.md* — an I/O path
(`/output/totals.txt`) and an output field name (`crossing_t`) were both
false-flagged as leaks, wrongly quarantining valid tasks (and hitting the hard
`scientific_computing` corner disproportionately, skewing admit rate). The
answer *value* lives in data files; that is the only thing checked. Cost: an
exact_text answer embedded solely in a test `.py` is not leak-checked by L —
that narrow residual falls to Gate B and the generator's "answer only in
tests/" rule.

**Gate B′ repair loop (amend 7 — Option B, chosen).** Every broken_test case in
the first real smoke batch had one root cause: the generator emits a reference
solution it never executed, so unmeetable thresholds (F1 target above what the
reference reaches), exit-127 scripts, and hallucinated APIs (`numpy.trapz`) slip
through. This is a *generator-quality* problem that Gate B′ correctly catches —
we are **not** wrongly rejecting valid tasks, so the gate is not loosened. But
rather than only quarantine, on B′ failure we run a **bounded repair loop**:
feed the model the *actual* verifier output (exit code, stderr, measured metric
vs. threshold) and ask it to fix the reference or lower the threshold to what the
reference genuinely achieves; **max 2 retries**; each repaired candidate is
re-probed through A + B + B′ (so a repair that breaks the build → `broken_test`,
or over-lowers the threshold into a pre-solved baseline → `pre_solved`);
still-failing after retries → `broken_test` as before. This is **execution-
feedback repair, NOT model self-check**: the three failures prove the model
cannot catch these by reading its own code, so the repair signal must come from
running it. `repair_attempts` (0–2) is recorded in `gate.json` so a high repair
rate stays visible as a base-prompt-quality signal instead of being masked — if
most tasks need repair, the generator prompt, not the loop, is the thing to fix.
Complementary prevention: the generator's hard requirement 5 now demands
reference-solution **self-consistency** (the reference must satisfy the stated
threshold/spec).

**Small-eval-set guess resistance (metric_threshold ≥ 30 items).** A leak-free
task can *still* be reward-hackable if its held-out set is tiny: with only a
few test items an agent can eyeball the visible inputs and hardcode plausible
outputs, clearing the threshold by guessing rather than by doing the work —
and Gate L sees nothing, because no answer was ever present to leak. This is a
distinct surface from file leaks. Mitigation: **every `metric_threshold` task
must ship ≥ 30 held-out test items**, large enough that guessing from inputs
alone won't reliably clear a well-chosen threshold. (Our exemplar ships 34; the
5-row original was brute-force guessable.) Enforced as a generator hard
requirement and worth a lightweight generator-side/gate assertion on
`len(test items)`.

| Gate | Check | Pass condition | On fail → | Paper analogue |
|---|---|---|---|---|
| **A buildable** | `docker build` (reuse `harness/sandbox.py:build_image`) | build exits 0 | `_quarantine/` reason `build_failed` | §3.1 build-executability gate (their only one) |
| **B not pre-solved** *(amend 1)* | run verifier on the **untouched** fresh container | fresh reward is **below the pass threshold** | `_quarantine/` reason `pre_solved` | RL drops all-passing groups (zero-std) |
| **B′ test-is-solvable** *(amend 2, NEW; +repair loop, amend 7)* | apply `solution_md`'s reference solution to a fresh container, run verifier; on failure run the bounded repair loop below | reference reward **reaches the pass threshold** (possibly after repair) | `_quarantine/` reason `broken_test` | none — new; disambiguates impossible-task vs. unsolvable-by-agent |
| **L answer-leak** *(amend 6, NEW)* | grep the **built image filesystem** and `task.md` for the reference answer / expected output that the verifier compares against | the reference answer is **absent** from both the image and `task.md` | `_quarantine/` reason `answer_leak` | none — new; automates the §D.6 reward-hacking guard |
| **C solvable-by-agent** *(amend 3)* | run the Phase 1 harness with the strong model (Sonnet-class), **full k = 4, NO early-stop** | **≥ 1 / 4** rollouts reach the pass threshold | `_unsolved/` *(amend 4)*, NOT quarantine | reward > 0 within 32 rollouts (§D.5), scaled to 4 |

Amendment 1 rationale: a task whose fresh-container baseline is *nonzero but
below threshold* (e.g. a `metric_threshold` task where the trivial output
already scores 0.4 against a 0.95 bar) is a perfectly **valid** task — the
agent still has real work to do. Only a baseline that already meets the bar is
pre-solved. `== 0.0` (the original proposal) would wrongly quarantine these.

Amendment 3 rationale: running the full k=4 without early-stop costs a little
more than early-stop, but the success count (0–4) recorded per task is a **free
preview of the pass@k curve** on the eval model we care about — worth the spend.

### Bucketing (amend 4)

- `tasks/` — admitted: passed A, B, B′, and C (Sonnet ≥ 1/4).
- `tasks/_quarantine/<id>/` — **broken**: failed A, B, B′, or L
  (`build_failed` | `pre_solved` | `broken_test` | `answer_leak`). Not eval
  material.
- `tasks/_unsolved/<id>/` — **built + valid test + Sonnet 0/4**: candidate
  genuinely-hard task. Kept *separate* from broken ones for manual review; may
  be rescued into `tasks/` if a human confirms it is solvable.

The `_quarantine` vs. `_unsolved` split is the whole point of B′: without it, a
0-reward task is ambiguous between "impossible/broken" and "hard". B′ collapses
that ambiguity before C runs.

### Network / flag parity (amend 5)

Gate C's episodes and real eval runs **must** launch containers with identical
flags — `--network none`, `--memory`, `--cpus`, and `--pids-limit` — or Gate C
measures solvability under conditions the eval never reproduces, quietly
biasing which tasks are admitted. Mandate: **one container-launch config
object, one code path**, shared by the gate and `harness/runner.py`. No
per-call flag drift permitted.

Implementation note: done ahead of the pipeline as a standalone `fix(sandbox)`.
`harness/sandbox.py` now defines `ContainerConfig(network, memory, cpus,
pids_limit)`; `Sandbox` takes one and `RunConfig.container()` builds it, so the
gate and `harness/runner.py` share a single launch path. `--pids-limit`
(default 512) is now on the `docker run` invocation — our only guard against
fork-bomb PID exhaustion under the memory cap.

**Known gap (build-time containers):** `build_image` runs `docker build` with
no `--network`, so build-time steps use the daemon's default (bridge) network
and are *less* sandboxed than run-time containers; the 600 s build timeout is
the only backstop. Acceptable because task authors control the Dockerfile and
all downloads happen at build time by design, but noted so it isn't mistaken
for full isolation.

### `gate.json` schema (sketch)

```json
{
  "gate_A": true,
  "gate_B_reward": 0.4,
  "gate_B_prime_reward": 1.0,
  "repair_attempts": 1,               // 0-2; Gate B' execution-feedback repairs used
  "gate_L_leak": false,               // true = reference answer reachable from image/task.md
  "gate_C_successes": 2,
  "gate_C_k": 4,
  "verdict": "admitted",              // admitted | quarantined | unsolved
  "destination": "tasks/",            // tasks/ | tasks/_quarantine/ | tasks/_unsolved/
  "reason": null                      // build_failed | pre_solved | broken_test | answer_leak | unsolved_by_agent | null
}
```

## 3. Generator prompt structure

One API call per signature, strong model (Sonnet-class). Two parts.

**System prompt (fixed):**
1. Role: author of terminal-agent eval tasks; the solver is a text-only model
   in a bash loop (one command/turn, 120 s/cmd, `--network none` at runtime,
   ~30 steps — mirror [[harness]] / decision 002 exactly).
2. Hard requirements, each mapping to a gate or harness rule:
   - Dockerfile `FROM <base-image-for-domain>` (given in the user turn); only
     `apt-get`/`pip` additions; **all downloads at build time** (runtime has no
     network).
   - `tests/` must FAIL on the fresh container and PASS after a correct
     solution (Gate B / B′ phrasing, stated explicitly).
   - Tests check outcomes not procedure; are not readable from `task.md`; do
     not depend on agent-side state.
   - `task.md` never mentions tests, test paths, or grading.
   - Verifier-kind contract (Table 9): `exact_text` → assert exact file/stdout
     content; `metric_threshold` → compute a numeric metric vs. a reference and
     assert `metric >= threshold`, with a threshold that demands real work but
     not perfection. **`metric_threshold` tasks must ship ≥ 30 held-out test
     items** (see the guess-resistance rule below). The reference/answer key
     lives only in `tests/`, never in the image (Gate L).
3. Output: a single JSON object, no prose —
   `{"task_md", "dockerfile", "tests": {"test_*.py": ...}, "solution_md",
   "fixture_files": {"path": ...}}`. **`solution_md` is now load-bearing**: it
   must be a *runnable* reference solution (Gate B′ executes it), not just
   prose. It is written to the task dir but never copied into the image.

**User prompt (rendered from the signature):** the signature one line per axis;
the `descriptions:` text for the sampled complexity buckets; the persona
("write the task as this user would ask it"); the 3–5 primitive skills ("the
solution must genuinely exercise each"); the domain base-image name and what is
already installed in it; and one per-verifier-kind worked exemplar (few-shot,
same JSON schema) from `pipeline/exemplars/`.

## 4. Paper under-specification flags (our authored calls)

1. **Skill-type / primitive-skill / persona lists** — never published (Table 8
   gives examples + cardinalities only; seeded from Pi et al. 2026 whose
   taxonomy is also not in this paper). We author them.
2. **Language weights** — "8 (weighted)" with no weights given; we bias toward
   python/bash to match our base images.
3. **Complexity bucket semantics** — only "intricate = 30–60 commands" is
   defined; our `descriptions:` blocks define short/moderate/complex.
4. **Generator prompt text + output format** — not in the paper at all (Fig. 2
   shows only the pipeline shape; the real prompt is presumably in the released
   repo, which we deliberately have not copied). JSON output is our choice, for
   a single parse path.
5. **`metric_threshold` threshold / reference selection** — Table 9 gives
   examples ("SSIM ≥ 0.95") but no selection procedure; we delegate to the
   generator ("real work, not perfection") and let Gates B/B′ catch degenerate
   choices.
6. **Task-validity criterion without RL** — the paper has none (soft
   filtering). Gates B, B′, C are our stand-in; B and B′ have no paper analogue.
7. **Per-domain base-image contents** — §3.1 says per-domain base images exist,
   not what is in them. We define minimal ones at build time (out of scope for
   this note).

## 5. Build order

`axes.yaml` (real lists) → sampler + tests → per-verifier-kind exemplars →
**[STOP]** → generator → gate (incl. the sandbox parity refactor) → ≤10-task
pilot batch. Mirrors the session's checkpoints.

Links: [[001-scope]] · [[data-pipeline]] · [[verifiers]] · [[harness]] · [[evaluation]]
