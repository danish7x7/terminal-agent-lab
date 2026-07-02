# 002 — Harness conventions the paper leaves unspecified

Status: accepted (Phase 1 implementation). Deviates from / fills gaps in:
[[harness]] (the two ⚠️ items).

The paper says "a simple harness based on mini-SWE-agent with persistent
shell" (§3.4) but never specifies the submit convention, output truncation, or
timeout-recovery semantics. We chose (without consulting the mini-SWE-agent
source — a WebFetch was declined, so these are our own conventions, documented
so they can be revised):

1. **Reply protocol**: exactly one fenced code block per assistant turn,
   containing one bash command. Zero or multiple blocks → the command is not
   executed; the model gets a `FORMAT ERROR` observation and the turn still
   counts against `max_steps` (so a model stuck in bad formatting can't loop
   forever).
2. **Submit marker**: the agent finishes by sending exactly
   `echo COMPLETE_TASK_AND_SUBMIT` as its command. It is detected by the
   parser and **not executed**; the episode ends with `stop_reason=submitted`.
3. **Output truncation**: observations are capped at `max_output_chars`
   (default 10,000 chars ≈ 2.5k tokens); we keep the head and tail halves and
   splice in `... [N chars omitted] ...`, since the middle of long dumps is
   usually the least informative.
4. **Command timeout (120 s, Table 13)**: on timeout the shell process is
   killed and restarted. The container survives (background processes live
   on), but shell-local state (cwd, env vars) is lost — the observation says
   so explicitly so the model can recover.
5. **Reward**: `reward = passed / (passed + failed + errors)` parsed from
   pytest's summary line, run on a fresh copy of `tests/` copied in *at
   verification time* (reward-hacking lesson, paper §D.6, [[verifiers]]).
6. **Pass definition**: pass ⇔ reward == 1.0. pass@k uses the unbiased
   estimator (Chen et al. 2021); raw rewards are logged per rollout so any
   other definition can be recomputed offline ([[evaluation]]).

Links: [[harness]] · [[verifiers]] · [[001-scope]]
