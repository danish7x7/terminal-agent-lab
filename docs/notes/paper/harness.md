# Agent Harness

The paper's harness for rollouts, SFT generation, and verification (§3.4, §C,
Table 13). This note doubles as the Phase 1 implementation reference.

## Harness choice (§3.4, §C, Table 12)

A **simple mini-SWE-agent-style harness with a persistent shell**. The same
harness is used for RL rollouts, SFT data generation, and verification (§4.1
"Infrastructure"). They rejected Terminus-2 (Terminal-Bench's usual default)
because it requires agents to send raw keystrokes, which is brittle for small
models (§3.4); Table 12 confirms on Haiku 4.5 (TB-Lite): ours 60.8, mini-SWE-
agent 61.4, Terminus-2 56.1. A simpler harness also reduces RL-training
complexity (§C). Harness choice matters but doesn't dominate: TMAX-9B gains
≥9 points across all four harnesses tested (Table 5).

## Everything Phase 1 needs

### Agent loop shape (§3.4; mini-SWE-agent, Yang et al. 2024)

1. Context starts with a system prompt + the task instructions
   (max prompt tokens: 2048, Table 13).
2. Each assistant turn, the model thinks and emits **one bash command**
   (mini-SWE-agent convention: a single command in a code block — no
   structured tool-call API, which is exactly what makes it robust for small
   models, §C).
3. The command runs in a **persistent shell** inside the task's container
   (state — cwd, env vars, background processes — carries across turns).
4. Command output is returned as the next user message; repeat.
5. Episode ends when the agent signals completion (mini-SWE-agent submit
   convention) or a cap is hit.
   ⚠️ Paper gap: exact submit marker and how command output is truncated
   before re-prompting are not specified — check the mini-SWE-agent repo when
   implementing; record the choice in a decision note.

### Limits (Table 13, "Tools" + "Data" rows)

| Knob | Paper value | Our Phase 1 value |
|---|---|---|
| Max tool/env steps | 64 | 30 default (spec), configurable |
| Bash tool (per-command) timeout | **120 s** | 120 s (spec matches) |
| Max prompt tokens | 2048 | task prompts kept short |
| Per-turn max tokens | 16384 | model-side max_tokens |
| Max total response length | 65536 (32768 for Qwen 3 8B) | token budget in config |
| Sampling temperature | 1.0 | configurable per model |

Sandboxes are Podman/Apptainer containers in the paper (§4.1); we use Docker.
Terminal-Bench additionally has per-task timeouts which the paper doesn't
override (§4.1 "Evaluation") — our tasks should carry a per-task wall-clock
timeout too.

### How the verifier produces reward

- After the episode ends, the task's **unit-test verifier** (generated with the
  task, Fig. 2) runs inside the container.
- Legacy `exact_text` tasks are binary pass/fail; the graded verifier kinds
  (metric_threshold, adversarial_corpus, fuzz_equivalence, multi_protocol)
  yield **continuously-valued rewards** (§1, §3.1 "Graded verifiers", Table 9;
  §D.5 speaks of "reward > 0", confirming non-binary rewards exist).
- Phase 1 implements this as: reward = fraction of task tests passed (spec),
  which reproduces binary behaviour for single-test tasks and supports graded
  verifiers later. See [[verifiers]].

### How pass@k is computed (§3.2 Table 1, §B.2 Fig. 9)

- Protocol: n rollouts per task (n=8 in Table 1; 8 per environment in §3.3),
  report **mean pass@k across tasks** for k ∈ {1, 4, 8}.
- ⚠️ Paper gap: the estimator formula is never written down. Standard
  practice (Chen et al. 2021, not cited here) is the unbiased estimator
  pass@k = E[1 − C(n−c, k)/C(n, k)] with c = #successful rollouts out of n.
  With n = k it degenerates to "any of the n rollouts passed". We adopt the
  unbiased estimator with n ≥ k — record in a decision note.
- "Pass" for graded rewards is not defined either; simplest consistent read:
  pass ⇔ reward == 1.0 (all tests green). Our runner should log raw rewards
  per rollout so we can recompute under any definition.
- Eval-noise practice worth copying: paper runs each evaluation 3× and reports
  mean ± stderr (§4.1 "Evaluation").

## What we replicate vs. skip

- **Replicate (Phase 1)**: the whole loop above — persistent shell in Docker,
  one-command-per-turn protocol, 120 s per-command timeout, post-episode
  verifier producing reward = pass fraction, JSONL results, pass@k runner.
- **Adapt**: max_steps 30 not 64, API models not local vLLM, Docker not
  Podman/Apptainer — see [[001-scope]]. Resource limits per container
  (CLAUDE.md rule) — the paper only worries about this at RL scale (§5.2).
- **Skip**: multi-harness generalization experiments (Table 5), Harbor/Daytona
  backends (§4.1), interleaved-thinking chat-template edits (§4.1
  "Hyperparameters" — RL-specific).

Links: [[verifiers]] · [[evaluation]] · [[data-pipeline]] · [[001-scope]]
