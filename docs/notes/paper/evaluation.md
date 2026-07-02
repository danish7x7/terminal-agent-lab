# Evaluation

How the paper measures models and datasets (§3.2, §4.1 "Evaluation", §B.2,
§B.3, §E.1).

## Benchmarks and infrastructure (§4.1)

- Development evals: **Terminal-Bench 2.1** and **TB-Lite**, via the Harbor
  framework with a Podman backend, on a single A100 node with vLLM.
- Headline numbers (Fig. 1, Table 16): **Terminal-Bench 2.0** with a Daytona
  cloud sandbox backend, 5 rollouts per prompt, timed-out runs restarted up to
  3×. Backend choice shifts scores (Daytona installs faster → fewer timeouts,
  §4.1); one RL run would cost ~$3,150 on Daytona (§4.1 fn. 4).
- **Each evaluation is run 3× and reported as mean ± stderr** (§4.1) — cheap
  noise control we should copy.
- Per-task timeouts are left at Terminal-Bench defaults; inference throughput
  therefore affects scores, hence the fixed single-A100 setup (§4.1).

## Dataset difficulty protocol (§3.2, Table 1) — what Phase 2 copies

Fix a judge model (Gemini-3-Flash-Preview), a **250-task subsample** per
dataset, **8 rollouts each**; report mean pass@1/@4/@8 across tasks, plus mean
turns and mean tokens/run. Full pass@k curves for k = 1–8 in Fig. 9 (§B.2):
curve height = absolute difficulty, curve slope = how much extra sampling
recovers. TMAX sits in the hardest band and has the lowest pass@8 (53%) — hard,
not merely high-variance. Estimator formula is not stated in the paper; see
[[harness]] for the estimator discussion (we use the standard unbiased one).

## Diversity metrics (§3.2, §B.3, Eq. 1)

Balance score per categorical axis: Balance = exp(H)/N ∈ [1/N, 1], the
normalized effective number of categories (1 = perfectly uniform). Preferred
over raw entropy because it is comparable across axes with different bucket
counts. Domain composition itself is judged by Gemini-3-Pro labeling every
task with one of the 9 domains (Fig. 3).

## Decontamination (§B.4, Table 11)

13-gram sliding window (stride 1) between dataset task descriptions and
TB 2.0 / TB-Lite task descriptions; a task is flagged if any window matches.
TMAX: 0% on both.

## Generalization evals (§4.3, Tables 4–6)

Beyond Terminal-Bench: SWE-Bench Verified and AIME'24/25 (both in-harness and
single-turn), four different harnesses (ours, OpenHands, mini-SWE-agent,
Terminus-2), and a second model family (Qwen 3 8B). Purpose: show RL taught
capabilities, not harness overfit.

## What we replicate vs. skip

- **Replicate (Phase 1)**: k-rollout runner with per-rollout rewards logged to
  JSONL; pass@k computed from those logs ([[harness]]); 3× repetition habit
  where budget allows.
- **Replicate (Phase 2)**: the Table 1 protocol scaled down — spec: pass@1/@4
  for a Gemini-Flash-class and a Haiku-class model on a **30-task subsample**
  of our ~100 generated tasks; plot the pass@k curve like Fig. 9; write up in
  `results.md` vs. the paper's Table 1 row (TMAX: 42%/50%/53%).
- **Maybe**: balance score (Eq. 1) over our axes — trivial to compute, nice
  plot for the portfolio README.
- **Skip**: Terminal-Bench leaderboard runs (non-goal), Harbor/Daytona
  backends, decontamination (our tasks are fully synthetic and we don't train
  on benchmarks), harness/task generalization studies (RL-specific).

Links: [[harness]] · [[data-pipeline]] · [[rl-recipe]] · [[001-scope]]
