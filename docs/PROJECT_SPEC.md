# PROJECT_SPEC — terminal-agent-lab

Replicate the two cheap, high-value contributions of the TMAX paper at small
scale: (1) a mini-SWE-agent-style eval harness, (2) the compositional
synthetic task pipeline. Measure difficulty with pass@k like the paper does.

## Current phase: 1

## Phase 1 — Eval harness (target: ~2 weeks)
Build `harness/`:
- Agent loop: system prompt + task instruction → model proposes a bash
  command → executed in a persistent shell inside a Docker container →
  output returned → repeat, up to `max_steps` (default 30) with per-command
  timeout (120s, matching paper Table 13).
- Verifier runner: after the loop ends, run the task's `tests/` inside the
  container; reward = pass fraction (supports graded verifiers later).
- Config: model name, temperature, max_steps, token budget — one YAML file.
- CLI: `uv run harness --task tasks/<id> --model <name> --k 4`
- Exit criteria: run 3 hand-written toy tasks end-to-end with two different
  API models; results land in `evals/results/*.jsonl`.

## Phase 2 — Compositional task pipeline (target: ~3 weeks)
Build `pipeline/`, mirroring the paper's 9 axes (paper Table 8):
- `axes.yaml`: domain (9), skill types, primitive skills, persona, language,
  task complexity (4 buckets), command complexity (3), fixture, verifier.
  Start with fixture=text_only and verifiers {exact_text, metric_threshold};
  add others later.
- Sampler: draw one value per axis → task signature.
- Generator: prompt a strong model with the signature → emit task dir:
  `task.md` (instructions), `Dockerfile`, `tests/` (verifier), `solution.md`
  (reference notes, never mounted into the container).
- Base images: one pre-built image per domain (paper §3.1) so per-task
  builds are fast.
- Exit criteria: 100 generated tasks that build successfully; measure
  Gemini-Flash-class and Haiku-class pass@1/@4 on a 30-task subsample;
  plot pass@k curve like paper Fig. 9; write up in docs/notes/results.md.

## Phase 3 (stretch) — SFT on a small model
- Generate trajectories with a strong model on our tasks; filter to
  successes; LoRA-SFT a 2–4B open model on a rented A100; re-run Phase 2
  eval before/after. Only start after Phase 2 exit criteria are met.

## Non-goals
- RL training (GRPO/DPPO), 14k-task scale, Terminal-Bench leaderboard runs.

## Definition of done (portfolio bar)
README with architecture diagram, one-command demo (`make demo`), pass@k
plot, and a short "what I learned vs. the paper" section.
