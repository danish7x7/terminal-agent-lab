# Journal

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
