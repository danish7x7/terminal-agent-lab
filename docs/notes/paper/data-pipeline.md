# Data Pipeline (TMAX-15K)

How the paper generates 14,600 RL terminal environments cheaply (§3, Fig. 2).

## Core idea: compositional generation

Each task is a product of **9 structured axes** (§3.1, Table 8). A sampler draws
one value per axis → a "task signature" → Gemini-3-Pro instantiates it into a
task directory: Dockerfile, unit-test verifier, source files, task instructions
(Fig. 2). Composing axes yields combinatorially many signatures with explicit
per-axis control over difficulty and diversity.

## The 9 axes (Table 8)

| Axis | Source | Cardinality | Notes |
|---|---|---|---|
| Domain | Pi et al. 2026 | 9 | security, software_engineering, file_operations, data_querying, data_science, debugging, scientific_computing, data_processing, system_administration |
| Skill type | Pi et al. 2026 | 4–7 / domain | e.g. Algorithmic, Systems, Web Security, Testing |
| Primitive skills | Pi et al. 2026 | 20–40 / domain | 3–5 sampled per task (e.g. "graph traversal and dependency resolution") |
| Persona | ours | 6–18 / domain | domain-tied user roles (e.g. "incident responder investigating a 3am page") |
| Language | ours | 8 (weighted) | Python, C, Bash, C++, Rust, Go, multi-language, any |
| Task complexity | ours | 4 | short, moderate, complex, intricate (30–60 commands) |
| Command complexity | ours | 3 | bash-only; bash + code; bash + code + system services |
| Fixture | ours | 7 | text_only, image, audio, video, stripped_binary, vendored_package, multi_service_compose (Table 10) |
| Verifier | ours | 5 | exact_text, metric_threshold, adversarial_corpus, fuzz_equivalence, multi_protocol (Table 9) — see [[verifiers]] |

First three axes are seeded from the Pi et al. (2026) skill taxonomy; the
remaining six are the paper's contribution (Table 8 caption).

## Three design principles (§3.1)

1. **Scalability via soft filtering.** No expensive teacher-based validation of
   generated tasks. The only hard check is *executability*: each task's Docker
   image must build. Broken/unsolvable tasks are filtered "for free" during RL,
   because groups with policy pass rate 0 contribute no gradient and are
   dropped. All-zero rate is low in practice: < 8 samples filtered per batch
   (§D.5, Fig. 11). ⚠️ This safety net **only exists because they do RL** — a
   key point for us, see [[001-scope]].
2. **Diversity via hierarchical sampling** plus two extra mechanisms:
   *persona diversification* (domain-specific personas, 5–18 per domain) and
   *multi-modal fixtures* — tasks ship a non-text artifact (PNG, audio, video,
   stripped binary, vendored package, compose stack; Table 10) that the
   text-only agent inspects via terminal tooling (tesseract, whisper.cpp,
   ffmpeg, objdump), so no multi-modal model is needed.
3. **Difficulty via explicit calibration**: the two complexity axes give
   granular control (sampled uniformly across buckets by default, with optional
   per-bucket up-weights for curricula), and graded verifier thresholds act as
   a continuous difficulty knob (§3.1, [[verifiers]]).

## Base images

Images are pre-configured **per domain**, so tasks in a domain share a base
image and only add task-specific dependencies (§3.1). This collapses the usual
two-step generate-then-validate approach into one cheap build step.

## How the data compares (§3.2)

- **Composition**: prior datasets concentrate 34–95% of mass on one domain
  (SWE-Smith: 95% software engineering); TMAX is near-uniform over all nine
  (Fig. 3). Domain balance score 0.998, skill-type 0.732 (Table 1; balance
  score = exp(H)/N, Eq. 1, §B.3).
- **Difficulty**: judged by Gemini-3-Flash-Preview on 250-task subsamples with
  8 rollouts each — TMAX pass@1 42% (prior work 41–92%), and the **lowest
  pass@4 (50%) and pass@8 (53%) of any dataset**, so difficulty persists as k
  grows (Table 1, Fig. 9, §B.2).
- **Decontamination**: 0% 13-gram overlap with Terminal-Bench 2.0 and TB-Lite
  task descriptions (Table 11, §B.4).

## SFT data (§3.3)

The same pipeline generated 2.2k extra environments; Qwen 3.6 27B produced 8
trajectories each → 16.5K trajectories (8K successful), used to warm-start
Qwen 3 8B (not Qwen 3.5, which it *hurt* — Table 7, §5.1). Trajectories with
unparsed tool calls are filtered out.

## What we replicate vs. skip

- **Replicate (Phase 2)**: the compositional sampler over all 9 axes
  (`axes.yaml`), signature → task-dir generation with a strong API model,
  per-domain pre-built base images, build-success as the executability gate.
- **Scale down**: ~100 tasks, not 14.6k (spec exit criteria; see [[001-scope]]).
  Fixtures start at `text_only` only; verifiers start with {exact_text,
  metric_threshold} (spec Phase 2).
- **Adapt**: we get **no RL soft-filtering**, so unsolvable/broken tasks stay
  in our eval pool and bias pass@k downward. Mitigation lives in [[001-scope]].
- **Skip**: SFT trajectory generation (§3.3) until Phase 3; multi-modal
  fixtures, difficulty curricula via bucket up-weights, and the balance-score /
  decontamination analyses (§3.2) — nice-to-have, not exit criteria.

Links: [[verifiers]] · [[harness]] · [[evaluation]] · [[001-scope]]
