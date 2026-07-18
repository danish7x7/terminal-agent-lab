# terminal-agent-lab

A scoped-down, single-developer replication of the data-generation and evaluation core of **TMAX** ([arXiv:2606.23321](https://arxiv.org/abs/2606.23321), *"A simple recipe for terminal agents"*). This project reproduces the paper's two cheap, high-value contributions at small scale: a **compositional synthetic task-generation pipeline** and a **terminal-agent evaluation harness** that measures task difficulty via pass@k. It deliberately omits the paper's reinforcement-learning training, which requires datacenter-scale compute (the paper reports ~8 H100 nodes and ~$3,150 per RL run in sandbox fees alone).

The goal is not to match the paper's 14,600-task dataset. It is to build the *machinery* the paper describes, understand it deeply enough to reproduce its central results (domain balance and graded difficulty), and document the engineering judgment involved at every step.

---

## Table of contents

1. [Motivation](#motivation)
2. [What this project is and is not](#what-this-project-is-and-is-not)
3. [Architecture overview](#architecture-overview)
4. [The evaluation harness](#the-evaluation-harness)
5. [The task-generation pipeline](#the-task-generation-pipeline)
6. [The validation gate](#the-validation-gate)
7. [Container safety model](#container-safety-model)
8. [Key engineering findings](#key-engineering-findings)
9. [Cost model](#cost-model)
10. [Current status and open problems](#current-status-and-open-problems)
11. [Repository layout](#repository-layout)
12. [Running it](#running-it)
13. [Design decisions and deviations from the paper](#design-decisions-and-deviations-from-the-paper)
14. [What I would do next](#what-i-would-do-next)

---

## Motivation

Terminal-using agents (Claude Code, Cursor, and similar) have become one of the most common applications of language models, but academic work on *how to train and evaluate them* is thin, largely because the benchmarks are hard, the data is scarce, and there is no simple baseline recipe. TMAX addresses this by generating a large, difficulty-controlled, domain-balanced dataset of terminal tasks and training small open models on it with reinforcement learning.

The paper's most reusable idea is not the trained model. It is the **compositional pipeline** that produces balanced, difficulty-aware tasks cheaply, and the **evaluation methodology** (pass@k over isolated Docker environments) that measures whether those tasks are actually hard. Those two pieces are reproducible by a single developer on a modest budget, and reproducing them exercises a genuinely useful skill set: synthetic data generation, container orchestration, agent-loop design, evaluation methodology, and cost-aware engineering.

This repository is that reproduction.

---

## What this project is and is not

**It is:**

- A working evaluation harness that runs a language model as a terminal agent inside isolated Docker containers and computes pass@k.
- A compositional task generator that samples across nine structured axes and materializes complete, runnable tasks (instructions, Dockerfile, tests, reference solution).
- A five-stage validation gate that filters generated tasks, standing in for the RL soft-filtering the paper relies on.
- A documented investigation into task difficulty, including a real open problem (difficulty bimodality) currently being diagnosed.

**It is not:**

- An RL training system. The paper's GRPO/DPPO training over 65k-token contexts is explicitly out of scope.
- A 14,600-task dataset. The target here is a balanced set on the order of 30–50 validated tasks, sufficient to reproduce the balance and difficulty analyses.
- A Terminal-Bench leaderboard entry. The harness is a mini-SWE-agent-style loop chosen for simplicity and small-model friendliness, not maximum score.

---

## Architecture overview

Three subsystems feed into one another:

```
  ┌─────────────────────┐      ┌──────────────────────┐      ┌─────────────────────┐
  │   GENERATOR         │      │   VALIDATION GATE     │      │   HARNESS           │
  │                     │      │                       │      │                     │
  │  sample signature   │─────▶│  A  image builds      │─────▶│  agent loop:        │
  │  across 9 axes      │      │  B  not pre-solved    │      │   model → command   │
  │                     │      │  B′ reference passes  │      │   → container shell │
  │  strong model       │      │  L  no answer leak    │      │   → observation     │
  │  authors task:      │      │  C  strong model      │      │   → repeat          │
  │   task.md           │      │     solves ≥1/k       │      │                     │
  │   Dockerfile        │      │                       │      │  verifier → reward  │
  │   tests/            │      │  (repair loop on B′)  │      │  k rollouts →       │
  │   solution.md       │      │                       │      │   pass@k            │
  └─────────────────────┘      └──────────────────────┘      └─────────────────────┘
         produces                    filters into                measures
       raw task dirs           admitted / _quarantine /       task difficulty
                                     _unsolved
```

The **generator** is the data factory. The **gate** is the quality filter (and the project's most original contribution, since the paper has no explicit validation step). The **harness** is the measurement instrument, and the gate reuses it internally for its solvability checks, so the same code path that evaluates a task also validates it.

---

## The evaluation harness

The harness implements a mini-SWE-agent-style loop, chosen over the more complex Terminus-2 harness because the paper finds (its §C, Table 12) that simpler harnesses perform better with small models, which struggle with elaborate tool-call formats.

**The loop.** The model receives a system prompt plus the task instructions, then on each turn:

1. Proposes exactly one bash command inside a single fenced code block.
2. The command runs inside a persistent shell in an isolated Docker container.
3. The output, exit code, and any truncation or timeout are formatted back as an observation.
4. The loop repeats until the model submits, hits the step limit, or exhausts a token budget.

**The persistent shell.** Commands run over a single long-lived `docker exec` bash process, so state (working directory, environment variables, background processes) persists across turns. A sentinel and exit-code capture delimit each command's output. On the 120-second per-command timeout, the shell is killed and restarted: container and background processes survive, shell-local state is lost, and the observation says so explicitly. This is a deliberate contract, documented as revisable, since the paper never specifies timeout semantics.

**The submit protocol.** The model submits by replying with a code block containing only the submit marker. This convention is not specified by the paper and was authored here; its edge cases turned out to matter (see [Key engineering findings](#key-engineering-findings)).

**Scoring.** After an episode ends, a verifier copies the task's tests into a location the agent never had write access to, runs them from there in a fresh shell, and computes reward as the fraction of tests that pass. Running an episode *k* times and aggregating gives pass@k, computed with the unbiased estimator from Chen et al. (2021):

```
pass@k = 1 − C(n − s, k) / C(n, k)
```

where `n` is the number of rollouts and `s` the number that succeeded, averaged across tasks. The paper never states its estimator; this is the standard defensible choice and matches the intent of its Table 1.

---

## The task-generation pipeline

Each task is sampled as a product of **nine structured axes**, following the paper's Table 8. The first three (domain, skill type, primitive skills) are seeded from the taxonomy the paper itself borrows from Pi et al. (2026); the remaining six target diversity and difficulty.

| Axis | Shape | Values (at this project's reduced scope) |
|---|---|---|
| Domain | flat, uniform | 9: security, software engineering, file operations, data querying, data science, debugging, scientific computing, data processing, system administration |
| Skill type | per-domain | 4–5 per domain, conditioned on the drawn domain |
| Primitive skills | per-domain | ~15 authored per domain; 3–5 sampled per task |
| Persona | per-domain | ~6 per domain (e.g. "incident responder investigating a 3am page") |
| Language | weighted | Python, Bash, C, C++, Go, Rust, multi, any (biased toward what base images carry) |
| Task complexity | flat, uniform | short, moderate, complex, intricate (up to 30–60 commands) |
| Command complexity | flat, uniform | bash-only; bash + code; bash + code + services |
| Fixture | flat | text_only (reduced from the paper's 7 multi-modal kinds) |
| Verifier | flat | exact_text, metric_threshold (reduced from the paper's 5) |

**Compositional sampling as the diversity mechanism.** Drawing one value per axis yields combinatorially many distinct task signatures, which is precisely what produces the paper's headline result: near-uniform domain balance (TMAX scores 0.998 on the balance metric versus 0.15–0.65 for prior datasets that pile most of their mass onto a single domain). A task's full signature, including the RNG seed, is stored as `signature.yaml` in each task directory for reproducibility and for the later balance-score computation.

**Generation.** One API call per signature to a strong model (Sonnet-class). The signature renders into a prompt with hard requirements that each map to a gate or harness rule, and the model returns a single JSON object containing the task instructions, a Dockerfile, a set of test files, a runnable reference solution, and any fixture files. The single-JSON output was chosen for a single parse path; the tradeoff (escaping fragility) is handled at parse time with a layered strict → escape-repair → json5 fallback rather than by switching to a delimiter format.

---

## The validation gate

This is the piece the paper does not have. TMAX skips task validation entirely because its RL training applies effective soft filtering: environments where the policy never succeeds contribute no gradient and are effectively dropped. Without RL, broken tasks would silently poison the dataset, so validation must be explicit.

Every generated task passes through five gates, cheap to expensive. A shared **pass-threshold** definition (1.0 for exact_text; the task's own threshold for metric_threshold) is referenced by all gates so they cannot drift.

| Gate | Check | Catches | Failure route |
|---|---|---|---|
| **A** buildable | `docker build` succeeds | broken Dockerfiles | `_quarantine/build_failed` |
| **B** not pre-solved | verifier on the untouched container scores *below* the pass threshold | tasks that pass with no work | `_quarantine/pre_solved` |
| **B′** reference valid | the generated reference solution, applied to a fresh container, *reaches* the pass threshold | broken or impossible tasks; broken tests that reject even a correct solution | repair loop, then `_quarantine/broken_test` |
| **L** no answer leak | the built image and task.md do not contain the verifier's reference answer | reward-hacking by reading the answer key | `_quarantine/answer_leak` |
| **C** solvable | a strong model, run through the harness, solves the task at least once in *k* rollouts | genuinely unsolvable tasks | `_unsolved/` (kept, not discarded) |

Two design choices distinguish this from a naive filter:

**The repair loop (on Gate B′).** When a reference solution fails its own tests, the *actual execution output* (exit code, stderr, measured-versus-threshold) is fed back to the model, which is asked to fix the reference or adjust the threshold to what the reference achieves. Up to two retries, re-probing A/B/B′ each time; the retry count is recorded in `gate.json` so a high repair rate stays visible as a base-prompt-quality signal rather than being masked. This is explicitly *not* model self-checking: the failures that motivated it (a hallucinated `numpy.trapz`, an exit-127 script, an unmeetable F1 threshold) are exactly the errors a model cannot catch by reading its own code. The repair signal comes from real execution.

**`_unsolved/` is separate from `_quarantine/`.** A task that builds, is not pre-solved, has a valid test, but that the strong model cannot solve is *potentially genuinely hard*, not broken. Those go to `_unsolved/` for manual review rather than being thrown in with broken Dockerfiles. This separation is the projection of two orthogonal signals that Gate B′ and Gate C together provide: *is the test sane* and *is the task agent-solvable*. Collapsing them would discard the most interesting tasks.

Every gate writes a durable `gate.json` carrying its verdict, the verifier output, and the reference-solution step outputs, so any quarantined task ships with the evidence of why it failed.

---

## Container safety model

Generated tasks contain model-authored Dockerfiles and code that run at volume, so the sandbox is hardened:

- **Network isolation.** Containers run with `--network none` at runtime; all downloads happen at build time. (Build-time containers use the daemon default network and are less sandboxed; the 600-second build timeout is the only backstop, documented as a known gap.)
- **Resource limits.** Every container is launched with `--memory`, `--cpus`, and `--pids-limit` (default 512). The PID limit specifically guards against fork-bomb process exhaustion, which a memory cap alone does not prevent.
- **No host mounts.** Nothing host-side is bind-mounted. The only host-to-container path is `docker cp`, used to copy fixtures and tests in at controlled points.
- **Structural parity.** A single `ContainerConfig` is constructed once and threaded through both the gate and the evaluation runner, so gate-time and eval-time containers use identical flags by construction. Parity is not something to remember; it is enforced by sharing one code path.
- **Anti-tamper verification.** At verify time, the tests directory is wiped and authoritatively re-copied from the never-mounted host, and tests run in a fresh shell. This closes the "plant a passing test" reward-hacking vector.

---

## Key engineering findings

The most valuable output of this project is not the code; it is a set of lessons, each an instance of the same meta-lesson: **real language-model output at temperature 1.0 fails in ways that unit tests written against a clean mental model never predict.** Each was caught, diagnosed from persisted evidence, fixed, and covered with a regression test.

**1. Small models fail the protocol, not just the task.** During the first real run, a small model replied with both solution commands and the submit marker in a single message. The parser saw the marker, declared submission, and silently discarded the commands, so a rollout that did real work recorded a zero. The fix reclassifies any mix of commands and the submit marker as a format error and feeds a corrective message back, letting the loop continue. The deeper lesson: a harness that merely rejects teaches nothing, but one that explains the error and allows recovery rescues the rollout. This reproduces the paper's own §C finding about why simple harnesses beat complex ones for small models.

**2. You cannot debug what you do not persist.** That first bug was initially undiagnosable because logging saved only summary rows, not the per-step transcript. Adding full per-rollout transcripts (model reply, parsed command, observation, exit code, format errors) turned an opaque failure into a five-minute diagnosis. The same lesson recurred later when an interrupted batch lost its `gate.json` files, after which gate verdicts were made durable.

**3. Real model output breaks your parser in ways you did not imagine.** Running the generator against a live model surfaced a class of JSON-validity failures no hand-written test predicted: a code-fence regex truncating at a nested fence, a brace-span heuristic overshooting into trailing prose, and un-doubled shell backslashes producing invalid JSON escapes. Roughly 40% of early generations did not parse. The fix layered a json5 fallback after escape-repair and, crucially, made every generation failure persist its cause (truncation versus malformed JSON) so future batches self-diagnose.

**4. A model cannot verify its own code by reading it.** The generator authored tasks whose own reference solutions failed: an F1 threshold its solution scored half of, a script that exited 127, and a call to a numpy function that does not exist in the installed version. All three passed a "does this look right" reading and failed on execution. This is the entire reason Gate B′ *runs* the reference in a real container instead of inspecting it, and the reason the repair loop's signal comes from execution output rather than self-reflection.

**5. A false-reject gate is the most dangerous kind, because it is silent.** A newly built Gate L false-positived on a legitimate output path, flagging it as a leaked answer. Had that run at scale without per-gate evidence being read by hand, every valid task with an I/O path would have been silently discarded and the dataset corrupted with no error raised. The lesson: gates are themselves code that can be wrong, and a filter that wrongly rejects valid data fails invisibly.

**6. Difficulty is not the same as length.** (Open finding, see below.) The generated tasks come out bimodal: a strong model either solves them perfectly or not at all, with nothing in the middle. This suggests the complexity axis, which controls command *count*, may be producing length rather than reasoning difficulty, and/or that all-or-nothing test structure makes graded reward impossible. This is currently under investigation.

---

## Cost model

The validation gate runs full model episodes inside containers, which makes it the dominant cost of the entire pipeline. A cost autopsy over a 17-task batch (derived entirely from persisted token counts, no additional model calls) established:

| Stage | Unit cost | Share of a 17-task batch |
|---|---|---|
| One generation call | ~$0.037 (est.) | 13% |
| One repair call | ~$0.037 (est.) | 8% |
| One Gate C episode | ~$0.073 (exact, 52 logged) | **79%** |

Gate C dominates because each admitted-track task runs *k* full episodes through it. Projected cost to reach 50 admitted tasks (at the observed ~65% admit rate) under three Gate C configurations:

| Gate C config | End-to-end total |
|---|---|
| k=4 Sonnet (original) | ~$22 |
| **k=2 Sonnet (chosen)** | **~$13** |
| k=4 Haiku | ~$10 (but changes what "admitted" means) |

The chosen configuration is **k=2 Sonnet**. Under the current perfectly-bimodal difficulty distribution, a 4/4 task is 2/2 and a 0/4 task is 0/2, so halving *k* changes no admit decision while halving the dominant cost. (This is flagged as revisitable: once the difficulty fix lands and tasks occupy the 1–3/4 band, k=2 will lose the pass-rate resolution that band is meant to provide, and a higher *k* may be needed.) A Haiku swap was rejected because Gate C measures "solvable by the Gate C model," so a weaker model would admit a different, easier set and change the meaning of the dataset.

This cost wall is not incidental. It is the exact limitation the paper's authors name in their own Limitations section: running many isolated containers remains expensive and can put terminal-agent work out of reach for small teams. Hitting it, measuring it, and engineering around it is part of what this project demonstrates.

---

## Current status and open problems

**Roughly 55–60% of the way to a finished portfolio deliverable** (a balanced dataset plus its balance and difficulty analyses plus a writeup).

**Complete:**

- Paper distilled into cited concept notes.
- Evaluation harness: agent loop, persistent shell, verifier, pass@k, fully tested and validated end-to-end across two models and three toy tasks.
- Compositional generator across all nine axes at reduced scope.
- Five-gate validator with execution-feedback repair loop.
- Container safety hardening with structural gate/eval parity.
- Cost model and a chosen cheaper Gate C configuration.
- A 17-task partial batch with per-bucket and difficulty analysis persisted.

**The critical open problem: difficulty is bimodal.** Every task a strong model reached scored either 4/4 (trivially solvable) or 0/4 (impossible), with nothing in between. The 0/4 tasks are correctly routed to `_unsolved`, which means the *admitted* set has zero difficulty for a strong model. This is a problem because the headline deliverable is a pass@k *difficulty curve*, and an all-or-nothing distribution cannot produce one. The paper's data shows graded difficulty (a strong model scoring 42% pass@1, not 0% or 100%).

Two hypotheses, both checkable against already-persisted data with no further spend:

1. **Verifier granularity.** If tasks ship only one or two all-or-nothing tests, reward is structurally 0 or 1 regardless of task hardness. The fix would require the generator to author multiple independent tests (partial-progress checks plus the full check) so a half-solved task scores partial reward.
2. **Complexity does not drive difficulty.** If the `task_complexity` axis controls command *count* rather than reasoning *subtlety*, then "intricate" tasks are simply long, and long tasks are either grindable (solved) or fragile (one error kills them), which reproduces the observed split. The fix would add a trickiness lever distinct from command count.

**Remaining after the fix:** generate the real 30–50 task dataset at k=2 Sonnet (~$13), compute the balance score and the pass@k difficulty curve against two models, line the results up against the paper's Table 1, and write the results section.

---

## Repository layout

```
terminal-agent-lab/
├── CLAUDE.md                    # project constitution / conventions
├── harness/
│   ├── config.py                # YAML + CLI config, shared ContainerConfig
│   ├── llm.py                   # Anthropic / OpenRouter client
│   ├── prompts.py               # system prompt + observation templates
│   ├── command_parser.py        # model reply → single bash command / submit
│   ├── sandbox.py               # Docker lifecycle, resource limits, no host mounts
│   ├── shell.py                 # persistent shell, per-command timeout
│   ├── episode.py               # the agent loop
│   ├── verifier.py              # reward = test pass fraction, anti-tamper copy
│   ├── runner.py                # k rollouts → unbiased pass@k → JSONL + transcripts
│   └── cli.py                   # `uv run harness ...`
├── pipeline/
│   ├── axes.yaml                # the 9 axes with authored per-domain lists
│   ├── sampler.py               # deterministic seeded signature sampler
│   ├── generator.py             # signature → task dir via strong model
│   ├── gate.py                  # A → B → B′ → L → C + repair loop
│   └── exemplars/               # one worked example per verifier kind
├── tasks/
│   ├── toy-{hello,pipeline,service}/   # hand-written sanity tasks
│   ├── <admitted tasks>/
│   ├── _quarantine/             # broken tasks, with evidence
│   └── _unsolved/               # valid-but-hard tasks, kept for review
├── evals/
│   ├── results/                 # pass@k JSONL
│   └── results/transcripts/     # per-rollout step transcripts
├── docs/
│   ├── PROJECT_SPEC.md          # phased plan
│   ├── notes/                   # Obsidian-style vault: paper notes, decisions, journal
│   └── review/                  # review packets, batch snapshots
└── pyproject.toml               # uv project
```

---

## Running it

Requires Docker (with the WSL2 backend on Windows), Python 3.11+, [uv](https://github.com/astral-sh/uv), and an `ANTHROPIC_API_KEY` in a `.env` file (never committed).

```bash
# install dependencies
uv sync

# run the full test suite (Docker integration tests included)
uv run pytest

# evaluate a single task: k rollouts of a model as a terminal agent
uv run harness --task tasks/toy-hello --model claude-haiku-4-5-20251001 --k 4
```

A run prints a JSON summary (successes, mean reward, pass@k) and writes a JSONL result plus per-rollout transcripts under `evals/results/`.

---

## Design decisions and deviations from the paper

The paper under-specifies several things; every deviation here is authored deliberately and documented in `docs/notes/decisions/`.

- **No RL training.** Out of scope; the paper's central contribution that this project reproduces is the data pipeline, not the trained model.
- **Reduced scale.** ~30–50 validated tasks rather than 14,600, sufficient for the balance and difficulty analyses.
- **Reduced axes.** `fixture` is limited to text-only (the paper's multi-modal fixtures are dropped) and `verifier` to two kinds (exact_text, metric_threshold).
- **Explicit validation gate.** The paper has no task-validation step because RL soft-filtering absorbs broken tasks; the five-gate validator is this project's stand-in, and Gate B (not-pre-solved) has no paper analogue at all.
- **Authored taxonomy.** The paper publishes axis *cardinalities and examples* but not the actual skill, primitive-skill, and persona lists (they trace to Pi et al. 2026, also not reproduced), so those lists are authored here.
- **Chosen conventions.** The submit marker, output truncation, timeout-restarts-the-shell semantics, the pass@k estimator, and the generator prompt and output format are all this project's choices, since the paper specifies none of them.

Seven under-specification points are collected and attributed in the pipeline design decision note.

---

## What I would do next

In priority order:

1. **Resolve the difficulty bimodality** (critical path). Run the two-hypothesis analysis on the existing batch, apply the indicated generator or verifier fix, and validate on a five-task test before spending on scale.
2. **Generate the real dataset.** 30–50 admitted tasks at k=2 Sonnet.
3. **Produce the headline analysis.** Domain and skill-type balance scores, and a pass@k difficulty curve across two models, compared directly against the paper's Table 1 and Figure 9.
4. **Stretch: light SFT.** LoRA-fine-tune a small open model on trajectories generated over the task set and measure a before/after difference on the eval subset. This is the one genuinely optional piece; the project stands as a portfolio deliverable without it.

---

*This project was built incrementally with heavy use of an AI coding assistant, with every design decision, gate, and bug fix reviewed and reasoned through by hand. The journal and decision notes under `docs/notes/` record that trail in full.*
