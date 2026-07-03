# batch6 — partial snapshot (17/30), stopped on request

Durable snapshot of the batch6 pipeline run (fresh seeds 301–330 through
generate → full gate A→B→B′→L→C), stopped after 17 tasks at the user's request.
Committed so the work isn't lost when the session scratchpad is cleared.

- `results.jsonl` — one row per completed task (seed, axis buckets, verdict,
  reason, repair_attempts, Gate C success count). The authoritative per-task log.
- `tasks/` — the materialized task dirs in their gate buckets: admitted (top
  level), `_quarantine/`, `_unsolved/`, and `_gen_failed/`. Each admitted/gated
  task carries its `gate.json` (with `verifier_output`, `repair_attempts`) and
  `signature.yaml`.

Run config: Sonnet generator + repair (max_tokens 16384, max 2 repairs),
Gate C = Sonnet k=4 no early-stop. Includes the fixes committed this session:
Gate L image-only (no task.md check), generator no-preamble, json5 parse
fallback. Seeds 301–317 completed; seed 317 finished cleanly during shutdown
(all 17 `gate.json` integrity-checked, 0 corrupt).

Verdicts: 11 admitted · 4 quarantined · 2 unsolved · 0 gen_failed · 0 answer_leak.
This is a partial run — not the basis for final admit-rate/cost conclusions.
