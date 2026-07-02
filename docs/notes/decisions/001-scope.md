# 001 — Scope: what we deviate from the paper and why

Status: accepted (baked into PROJECT_SPEC.md). Deviates from: [[rl-recipe]],
[[data-pipeline]], [[harness]], [[evaluation]].

Goal restated: replicate the paper's two *cheap* contributions — the harness
and the compositional data pipeline — as a portfolio artifact. Depth of
understanding over scale.

## Deviation 1: API models instead of RL-trained open models

- **Paper**: trains Qwen 3.5 2B–27B with DPPO on H100 nodes, 2–3 days per run
  ([[rl-recipe]], §4.1).
- **Us**: evaluate off-the-shelf API models (Anthropic / OpenRouter) through
  the same style of harness.
- **Why**: no local GPU; an RL run needs ~8 H100 nodes (§4.1) and the paper
  itself estimates ~$3,150 per run on cloud sandboxes alone (§4.1 fn. 4). The
  transferable skills here are the harness and pipeline, not babysitting a
  training cluster. API models also give a *stronger* difficulty judge — the
  paper itself uses Gemini-3-Flash for exactly this (Table 1).
- **Cost**: we lose the paper's headline result (RL lifts a 9B model to 27%
  TB 2.0) and can't observe training dynamics (Figs. 5–8). Those live in
  [[rl-recipe]] as concepts.

## Deviation 2: ~100 tasks, not 14,600

- **Paper**: 14.6k environments, needed to fill RL batches for 500 steps with
  group size 32 (Table 13).
- **Us**: ~100 generated tasks (Phase 2 exit criteria), eval subsample of 30.
- **Why**: we only need enough tasks to *measure* difficulty and diversity,
  not to train on. The paper's own dataset-comparison protocol uses a 250-task
  subsample (Table 1) — so ~100 tasks with 4–8 rollouts is the same
  methodology at ~2.5× smaller scale. Generation and eval both cost API money
  (CLAUDE.md caps generation at 10/run for this reason).
- **Cost**: noisier pass@k estimates; can't meaningfully report balance across
  all 9×(4–7)×… axis combinations — but per-axis marginals still work.

## Deviation 3: no RL training code (GRPO/DPPO)

- **Paper**: DPPO + FP32 LM head + group size 32 is the core recipe (§4.1,
  §5.2).
- **Us**: none of it; explicit non-goal (PROJECT_SPEC, CLAUDE.md). Stretch
  Phase 3 is LoRA-SFT only, following the paper's §3.3/§D.2 SFT setup.
- **Why**: compute, and the paper's finding that this is the *unstable, hard*
  part (§5.2) — poor effort/insight ratio for a solo portfolio project. The
  concepts are captured in [[rl-recipe]].
- **⚠️ Knock-on effect — the one that changes our design**: the paper skips
  task validation because RL soft-filters broken tasks (all-zero groups drop
  out of the gradient, §3.1, §D.5). **We have no such filter**: an unsolvable
  generated task silently deflates our pass@k numbers instead of being
  ignored. Mitigation for Phase 2: (a) keep the paper's build-must-succeed
  gate; (b) run a strong model once per task and flag never-solved tasks for
  manual review before they enter the eval set (a cheap, explicit version of
  the paper's implicit filtering — the paper notes most TMAX-15K tasks get
  reward > 0 within 32 rollouts, §D.5); (c) log raw rewards so bad tasks can
  be excluded retroactively.

## Deviation 4 (minor): harness knobs

- max_steps 30 (spec) vs. the paper's 64 tool steps (Table 13) — our toy/
  generated tasks skew shorter than "intricate (30–60 commands)" tasks; 64 at
  API prices doubles cost for little signal. Configurable, so we can raise it
  for the complex-bucket tasks later.
- Docker (Desktop/WSL2) instead of Podman/Apptainer (§4.1) — environment
  constraint, functionally equivalent for our purposes.
- 120 s per-command timeout kept identical to Table 13.

Links: [[harness]] · [[data-pipeline]] · [[verifiers]] · [[evaluation]] · [[rl-recipe]]
