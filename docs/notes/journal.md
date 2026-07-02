# Journal

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
