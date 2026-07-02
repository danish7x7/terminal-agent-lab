# RL Recipe (concepts only — we do NOT implement this)

The paper's training side (§4, §5, §D). Out of scope per PROJECT_SPEC
non-goals; kept as understanding/interview material.

## Algorithm (§4.1)

- **DPPO** (Qi et al. 2026), a GRPO variant that **masks tokens whose
  inference vs. training logprobs deviate** (binary approximation of total
  variation divergence, threshold 0.1, Table 13). Naive GRPO collapses in
  long-horizon agentic training; DPPO limits the collapse (Fig. 7, §D.4).
- Token-level loss (DAPO-style, Yu et al. 2025), fully asynchronous training,
  zero-std groups filtered, active sampling to keep batches full (following
  Olmo 3).
- Outcome-only reward (no process reward), KL coefficient β = 0 — a small KL
  penalty reduced collapse severity but lowered final reward (§5.2).

## Key hyperparameters (Table 13)

Group size **32** rollouts/prompt (larger groups stabilize — Fig. 8), 8
prompts/batch, max sequence 65536, **max 64 tool steps, 120 s bash timeout**
(these two matter for our [[harness]]), LR 1e-6 constant, 500 steps, best
checkpoint by TB-Lite every 100 steps, temperature 1.0, FP32 LM head.

## Stability lessons (§5.2, Fig. 4)

1. **Training–inference numeric mismatch** is the villain: FP32 LM head
   dramatically cuts vLLM-vs-trainer logprob divergence for Qwen 3.5 (Fig. 4).
2. **Multi-turn exacerbates instability**: issues appear past ~10 assistant
   turns, absent under 5; runs often collapse past 300 steps.
3. **Infra contention is a training signal problem**: sandboxes co-located
   with inference nodes → slow commands the model never sees at eval; models
   sometimes showed "awareness" of infra conditions (§5.2).

## SFT warm-start findings (§3.3, §5.1, Tables 6–7)

- Qwen 3 8B needs SFT warm-start (7.3 → 11.5 TB-Lite, then RL → 17.7).
- Qwen 3.5 9B is *hurt* by SFT — both by TMAX-SFT (41.9 → 35.5) and a 327K
  "big mix" of prior datasets (→ 31.3, Table 15) — likely already heavily
  post-trained, and prior datasets used weak teachers (§5.1). So the headline
  models are RL-from-base, no SFT (§4.1 "Hyperparameters").

## Results that motivate the data work (§4.2–4.3)

- Same recipe, different datasets: TMAX-15K beats all six prior datasets
  (TB-Lite 57.2, TB 2.1 28.8 vs. ≤53.0/25.5; Table 2), attributed to
  persistent difficulty — average steps/episode stays higher throughout
  training (Fig. 5); per-turn tokens grow, i.e. learned inference-time scaling
  (Fig. 6).
- TMAX-9B: 27% TB 2.0, best <10B, near Haiku 4.5 (Fig. 1, Table 16).
- Generalizes across tasks (SWE-Bench Verified +9.5, AIME 73.3 → 91.1;
  Table 4), harnesses (≥+9 on all four; Table 5), and model families (Qwen 3;
  Table 6) — evidence against mere harness-fitting.

## What we replicate vs. skip

- **Skip (non-goal)**: all of it — DPPO/GRPO, asynchronous infra, FP32-head
  tricks, curriculum. Explicitly excluded by PROJECT_SPEC non-goals and
  CLAUDE.md.
- **Concepts we reuse anyway**: Table 13's harness-facing knobs (64 steps /
  120 s timeout → [[harness]]); "soft filtering only works under RL" is the
  core reason our scope decision needs a task-validity mitigation
  ([[001-scope]]); pass@k-vs-k curves as a difficulty lens ([[evaluation]]).
- **Phase 3 (stretch) borrows**: the SFT setup (§3.3, §D.2, Table 14 — 2
  epochs, LR 2e-5, success-filtered trajectories) is roughly what our
  LoRA-SFT stretch goal would follow, minus the RL that comes after.

Links: [[harness]] · [[data-pipeline]] · [[evaluation]] · [[001-scope]]
