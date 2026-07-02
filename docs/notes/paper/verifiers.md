# Verifiers

How TMAX tasks are checked and rewarded (§3.1 "Graded verifiers", §B.1,
Tables 9–10).

## Why graded verifiers

Previous RL terminal tasks rely on exact string equality against a ground
truth (§3.1). TMAX keeps that as the legacy default and adds four graded kinds
that (a) relax brittle string matching, (b) expose a **continuous difficulty
knob**, and (c) naturally extend task length via multi-condition variants
(§3.1, §B.1). Each task samples exactly one verifier kind and one fixture kind
independently (§B.1).

## The five kinds (Table 9)

| Kind | Pass criterion | Example | Difficulty knob |
|---|---|---|---|
| exact_text | output exactly equals ground-truth string | file contents match a reference | — (legacy) |
| metric_threshold | numeric metric vs. reference meets threshold | image SSIM ≥ 0.95; speedup ≥ 1.3× | threshold value |
| adversarial_corpus | rejects every malicious item AND preserves every benign item | sanitiser blocks exploits, passes clean input | per-corpus pass rate; corpus size |
| fuzz_equivalence | program matches reference oracle bit-exactly on N random inputs | reproduce a stripped binary's output | N; input distribution |
| multi_protocol | agent-launched service answers real protocol-level requests | HTTP / TCP / gRPC / SMTP checks | number of protocols/conditions |

Mechanically, the verifier is a **unit-test suite generated alongside the
task** (Fig. 2) and run in the container after the episode; graded kinds yield
continuously-valued rewards rather than 0/1 (§1, §3.1; see [[harness]] for the
reward plumbing).

## Fixtures interact with verifiers (Table 10)

Non-text fixtures hide the ground truth inside an artifact (PNG → tesseract,
audio → whisper.cpp, video → ffmpeg, stripped binary → objdump/gdb/strings,
vendored package → offline build/debug, compose stack → service glue). The
verifier still checks recovered text/behaviour, so the policy stays text-only
(§3.1 "Multi-modal fixtures").

## Reward hacking (§D.6)

Light manual check on TB 2.0 runs found 3 hacking patterns from TMAX-9B
(absent in the base model): replacing a checker file with a no-op, stubbing a
fake `caffe` binary + fake logs, mock `povray` wrappers. All scored 0 anyway
(TB tests caught them). CoT showed the model "simplifying" the task rather
than deliberately fooling the verifier. Lesson for our generated tasks:
**verifiers must not be writable/replaceable by the agent** — keep tests
outside the agent's reach until verification time (our spec already keeps
`solution.md` unmounted; tests should be copied in fresh at verify time).

## What we replicate vs. skip

- **Replicate (Phase 2)**: `exact_text` and `metric_threshold` (spec Phase 2
  start set). Verifier-as-test-suite with reward = pass fraction lands in
  Phase 1 ([[harness]]), so graded rewards work from day one.
- **Later, maybe**: adversarial_corpus, fuzz_equivalence, multi_protocol —
  spec says "add others later"; they need corpora/oracles/services, i.e. the
  expensive ones.
- **Skip**: non-text fixtures (spec starts fixture=text_only); the threshold-
  as-curriculum knob only pays off for RL training, though we can still use it
  to tune eval difficulty.

Links: [[harness]] · [[data-pipeline]] · [[001-scope]]
