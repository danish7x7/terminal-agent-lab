# Journal

## 2026-07-02 — Generator output validity: diagnose truncation vs malformed

**Diagnosed first**: the two `gen_failed` seeds from the last smoke were NOT
token-ceiling truncation — re-requesting at the same 8192 ceiling showed
output of 6066 and 4297 tokens (well under), and both happened to parse on the
retry. So the original failures were *stochastic malformed-but-complete JSON*
(trailing comma / comment / stray quote), a different bug class than the
escape-repair already done, and no `max_tokens` change fixes it. Recorded the
token counts so the call was evidence-based, not a guess.

**Fixed by cause**: (1) a `json5` last-resort parse fallback — string-aware, so
it absorbs the malformed-but-complete cases models actually emit (trailing
commas, `//` comments, unquoted keys) without the corruption risk of hand-rolled
regex; the strict → escape-repair → json5 chain now covers all observed modes.
(2) `classify_generation_failure` tags every gen-failure as `truncation` vs
`malformed_json` with the parse-error type and the raw tail, persisted so future
batches self-diagnose instead of needing a manual re-look. (3) raised generation
`max_tokens` to 16384 as cheap headroom (insurance, not the fix — truncation
wasn't happening).

**Format tradeoff (my read, unchanged pending your call)**: keep the single
JSON blob. Truncation isn't the pressure (4–6k tokens under an 8k ceiling, now
16k), and the blob's real weakness — escaping/validity — is better handled at
*parse* time (repair + json5) than by switching to a delimiter/heredoc file
format. A format change is a real refactor with its own parser and loses schema
validation; only worth it if intricate tasks start truncating even at 16k.

**Interview takeaway**: "invalid JSON from the model" is not one bug — it's at
least three (truncation, bad escapes, malformed-but-complete), and they need
three different fixes (bigger ceiling, escape repair, lenient parse). Lumping
them as "add a JSON repair" would have raised max_tokens for a problem that
wasn't truncation. Diagnosis before fix, with the token count as the
discriminator, is the whole game.

## 2026-07-02 — A newly-built gate wrongly rejected a valid task (Gate L)

**What happened**: the first run of the freshly-built validation gate
quarantined a perfectly valid debugging task as `answer_leak`. Root cause: Gate
L's needle extraction pulled `/output/totals.txt` — an *I/O path the task states
in task.md by design* — out of a test string literal and matched it against
task.md. The "answer" it "found leaking" was the output path, not the answer.
Fix: leak needles now exclude path-like strings (containing `/`), documented as
a Gate L limitation. Re-running the same task post-fix: A✓ / B=0.0 / B′=1.0 /
L=clean / **C=4/4 → admitted** — the full path completes.

**Why it matters (the lesson)**: *gates are tasks too, and false-rejects are
silent.* A gate that wrongly quarantines looks identical from the outside to a
gate correctly filtering junk — the task just isn't in `tasks/`. Without the
durable per-gate evidence (`gate.json` recording the exact needle and verdict),
this would have been invisible: we'd have shipped a gate that quietly discards a
fraction of good tasks and called the low yield "generation quality". The same
principle that makes the eval trustworthy — persist why, per unit — is what
makes the *gate* auditable. Build the observability into the filter, not just
the thing being filtered.

## 2026-07-02 — Phase 2 gate: A→B→B′→L→C with an execution-feedback repair loop

**Built**: `pipeline/gate.py:run_gate` — the full validation gate from
[[003-pipeline-design]], Option B. Gate A build, B not-pre-solved (fresh reward
below the pass threshold), B′ reference-solution-passes with a **bounded repair
loop** (max 2 retries feeding the model the real verifier output — exit code,
stderr, measured-vs-threshold — then re-probing A+B+B′), L answer-leak (grep the
image + task.md for distinctive answer strings), C solvable-by-agent (k=4, no
early-stop, via `harness.runner.run_task` on the shared container config).
Tasks move to `tasks/`, `tasks/_quarantine/`, or `tasks/_unsolved/` with a
durable `gate.json` (now including `repair_attempts`, `verifier_output`, and the
reference-solution step outputs — the exact evidence that was missing from last
run). Added a reference-solution **self-consistency** requirement to the
generator prompt. 7 gate unit tests for the pure helpers.

**Why**: the smoke batch's three broken_test cases were all one root cause — the
generator ships a reference it never executed. That's a generator-quality
problem the gate correctly catches, so no loosening; instead the repair loop
converts a chunk of those into admissions using real execution feedback, and
`repair_attempts` keeps the underlying prompt-quality signal visible.

**Interview takeaway**: the three JSON-robustness bugs and these three
self-inconsistency modes (unmeetable threshold, exit-127 script, hallucinated
`numpy.trapz`) are the *same* lesson wearing two hats — real model output at
temp 1.0 fails in ways no unit test predicts, and the only reliable oracle is
execution. That's why the repair loop is built on the verifier's output and not
on asking the model to re-read its code: a model that could spot "trapz doesn't
exist" by reading would not have written it. Design the feedback signal to come
from the world, not from the model's self-report.

## 2026-07-02 — Phase 2 generator: prompt + parse + materialize

**Built**: `pipeline/generator_prompt.py` (system prompt with the hard
requirements each mapping to a gate/harness rule + signature-rendered user
prompt embedding the matching per-kind exemplar), `pipeline/generator.py`
(prompt a strong model → parse the single JSON object → materialize a task dir
with `signature.yaml`, `solution.md` kept out of the image), and
`pipeline/base_images.py` (per-domain base, uniform for now). 18 generator
tests, all API-free via a fake client.

**Why**: [[003-pipeline-design]] §3 — the generator is the last piece before
the gate; one task per signature, single-JSON output, ≥30 items for
metric_threshold, answer only in `tests/`, `task.md` silent on grading.

**Verified against real Sonnet output** — and that is where the value was. A
5-task smoke batch (in scratchpad, not committed) exercised the gates for real:
1 task passed A+B+B′ cleanly through to Gate C, 3 were correctly quarantined
`broken_test` (reference solution didn't reach the threshold), 1 gen-failure.
Real output surfaced **three JSON-robustness bugs** the unit tests missed, each
fixed with a regression test: (1) a ```json fence regex truncated at the
```bash fence *inside* solution_md; (2) first-`{`-to-last-`}` span overshot into
trailing prose containing a `}` → switched to `raw_decode`; (3) the model
emitted un-doubled shell/regex backslashes (`\\d`) that are invalid JSON escapes
→ added a repair pass that doubles only invalid escapes. Also fixed a
self-inflicted prompt bug (the output schema was shown as JSON *with `//`
comments*, inviting the model to emit comments) and made `fixture_files`
optional (a no-input task is valid).

**Interview takeaway**: you cannot unit-test a generator into correctness — the
failure modes live in the distribution of a real model's output, not in your
head. Every one of the three parser bugs passed a hand-written test and died on
the first real Sonnet call. The lesson isn't "write more tests", it's "put the
real generator on the real model early and cheaply (5 tasks, scratchpad) and
let the gate tell you the truth." The gate's broken_test bucket is also doing
exactly its job: generation quality at temp 1.0 is noisy, and the pipeline is
designed to filter, not to trust.

## 2026-07-02 — Phase 2 build starts: sandbox parity, axes, sampler, exemplars

**Built**: (1) the amendment-5 safety refactor as a standalone `fix(sandbox)` —
`ContainerConfig(network, memory, cpus, pids_limit)` built once by
`RunConfig.container()` and threaded through `Sandbox`, so the gate and
`harness/runner.py` share one `docker run` flag path; added `--pids-limit`
(512) as the fork-bomb guard that was missing. (2) `pipeline/axes.yaml` with
real authored lists at reduced scope (9 domains × skill_type/primitive/persona,
weighted languages, text_only fixture, {exact_text, metric_threshold}). (3) a
deterministic `pipeline/sampler.py` (flat / weighted / per_domain shapes,
domain-conditioned axes resolved after domain) with 11 tests. (4) two worked
generator exemplars (`exact_text`, `metric_threshold`) in the JSON schema
decision 003 mandates.

**Why**: [[003-pipeline-design]] build order — freeze the container-flag path
before running generated code, then the sampler is the diversity mechanism and
the exemplars are the few-shot spine of the generator prompt.

**Verified**: `uv run pytest` green (55 tests: 40 harness/sandbox + 11 sampler +
the exemplar checks below); both exemplars *built in real containers* and
confirmed to fail on the fresh image (Gate B: reward 0.0) then pass after their
reference solution runs (Gate B′: reward 1.0).

**Interview takeaway**: the metric_threshold exemplar surfaced a real design
subtlety — our verifier returns reward = pytest pass-fraction, so a graded
"accuracy ≥ 0.80" threshold has to live *inside* the test assertion, and the
held-out answer key has to ship in `tests/` (copied in only at verify time by
`verifier.py`), never in the image — otherwise the agent could just `cat` the
answers (the paper's reward-hacking failure mode, §D.6). Where the ground truth
physically lives is a security property, not a detail.

## 2026-07-02 — Phase 2 design frozen: decision 003

**Built**: [[003-pipeline-design]], the authoritative Phase 2 pipeline spec —
`axes.yaml` schema (3 axis shapes over the paper's 9 axes at reduced scope),
the generator prompt structure, and a five-gate validation pipeline with the
seven paper-under-specification flags. Five amendments over the original
proposal fold in: (1) Gate B checks the fresh baseline is *below the pass
threshold*, not `== 0.0`, so a nonzero-but-below baseline stays valid; (2) new
Gate B′ runs the reference `solution_md` and requires it to pass, splitting
"broken test" from "unsolvable"; (3) Gate C runs full k=4 with no early-stop,
recording Sonnet's 0–4 success count as a free pass@k preview; (4) C-only
failures go to `tasks/_unsolved/`, kept apart from `_quarantine/`; (5) gate and
eval must share one container-launch config (identical `--network none`, memory,
cpus, pids-limit) so Gate C can't measure solvability under conditions eval
never sees.

**Why**: [[001-scope]] Deviation 3 — with no RL gradient we get no free
soft-filtering of broken tasks, so the gate *is* the mitigation. Freezing the
contract before writing the sampler/gate prevents rework, especially the
sandbox parity refactor (today `harness/sandbox.py` hardcodes run flags and
sets no `--pids-limit`).

**Interview takeaway**: the sharp idea is Gate B′. A task scoring 0 is
ambiguous — impossible, or just hard? Running a *known-good* reference solution
turns that one ambiguous signal into two orthogonal ones (is the test sane × is
the agent capable), which is what lets `_quarantine` (throw away) and
`_unsolved` (keep, review) be different buckets. It's the same move the paper
leans on implicitly — reward > 0 within 32 rollouts (§D.5) — but made explicit
because we can't afford 32 and can't tell impossible from hard without an
oracle.

## 2026-07-02 — First real-model bug: mixed submit replies + transcript logging

**Built**: investigated toy-pipeline rollouts 1 & 3 (Haiku, step-1 submit,
reward 0). Root cause: the rev-1 parser matched the submit marker against only
the *first line* of the code block, so a reply mixing the marker with solution
commands was accepted as an instant submit and the work silently discarded.
Fixed per [[002-harness-conventions]] rev 2: submit is only valid as the sole
content of the reply's single block; any command+marker mix is a new
`mixed_command_and_submit` format error fed back as "run commands and submit
in separate messages". Also added the missing observability: full per-step
transcripts now land in `evals/results/transcripts/*.json`, linked from each
JSONL row — the original bug was undiagnosable from summary rows alone.

**Evidence**: re-ran toy-pipeline k=4 with Haiku — pass@1 went 0.25 → 1.0
(4/4). Rollout 1's first reply hit the new error live: Haiku hallucinated an
entire multi-turn session in one message (commands, fake outputs, submit),
got the corrective feedback, and recovered to solve in 8 steps.

**Interview takeaway**: small models don't just fail tasks, they fail the
*protocol* — the harness's format-error feedback loop is doing real work
(here worth 0.75 pass@1 on a trivial task). This is exactly why the paper
found simple harnesses beat Terminus-2 for small models (§C, Table 12): every
bit of protocol strictness must come with a recovery path, not a silent
misparse.

## 2026-07-02 — Phase 1 harness implemented

**Built**: the full `harness/` package per the approved file tree — config
(YAML + CLI overrides), Anthropic/OpenRouter clients over httpx, mini-SWE-agent
style prompt + single-code-block parser, Docker sandbox with resource limits
and no host mounts, persistent shell over one long-lived `docker exec` with
sentinel-delimited output and kill-and-restart on the 120 s timeout, agent loop
([[harness]] contract), pytest-based verifier (reward = pass fraction, tests
copied in fresh at verify time per §D.6), pass@k runner writing JSONL to
`evals/results/`, and `uv run harness` CLI. Three toy tasks (toy-hello,
toy-pipeline, toy-service) each stress a different capability. 30 tests:
22 pass locally, 8 Docker-marked tests auto-skip. Conventions the paper leaves
unspecified are recorded in [[002-harness-conventions]].

**Blocked on**: Docker is not visible in this WSL distro — Docker Desktop's
WSL integration needs to be enabled (Settings → Resources → WSL integration)
before the docker-marked tests and the end-to-end exit criterion (3 toy tasks
× 2 API models) can run.

**Interview takeaway**: a "persistent shell" is the harness's hardest design
corner — the timeout path conflicts with persistence. Killing a hung command
means killing the shell that holds the session state, so the honest contract
is "container state survives, shell state doesn't, and the model is told" —
a nice example of surfacing infrastructure reality to the policy instead of
hiding it (the paper hits the same theme with models noticing infra load,
§5.2).

## 2026-07-02 — Paper distillation

**Built**: populated `paper/` with the five concept notes — [[data-pipeline]],
[[harness]], [[verifiers]], [[rl-recipe]], [[evaluation]] — every claim cited
to a section/table, each ending with a "what we replicate vs. skip" section
keyed to the spec's phases. Wrote [[001-scope]] documenting our deviations
(API models not RL, ~100 tasks not 14.6k, no GRPO/DPPO, max_steps 30 not 64).
Extracted the full Phase 1 harness contract into [[harness]]: mini-SWE-agent
loop shape, one bash command per turn in a persistent shell, 120 s per-command
timeout (Table 13), verifier runs post-episode with reward = pass fraction,
pass@k = mean over tasks of the unbiased estimator from n rollouts.

**Why**: CLAUDE.md makes the notes the source of truth before any code; Phase 1
implementation starts from [[harness]], not from the PDF.

**Two paper gaps found** (flagged ⚠️ in [[harness]]): the exact episode-submit
marker and the per-turn output-truncation rule aren't in the paper — must be
lifted from the mini-SWE-agent repo and recorded as a decision. The pass@k
estimator formula is also never stated; we assume the standard unbiased one.

**Interview takeaway**: the paper's "skip validation, let RL soft-filter
broken tasks" trick (§3.1) is a *training-only* luxury — zero-pass groups
contribute no gradient, so bad tasks are free. In an eval-only replication the
same bad tasks silently deflate pass@k, so we need an explicit stand-in:
build gate + one strong-model rollout per task + retroactive exclusion via
logged raw rewards ([[001-scope]], Deviation 3).
