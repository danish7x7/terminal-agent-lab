# Notes Vault

Obsidian-style vault for terminal-agent-lab. Open this `docs/notes/` folder
directly as a vault in Obsidian if you like — Claude Code reads and writes
these as plain markdown either way.

Structure:
- `paper/` — distilled TMAX paper notes, one file per concept:
  [[data-pipeline]], [[harness]], [[verifiers]], [[rl-recipe]] (concepts
  only — we don't implement RL), [[evaluation]]
- `decisions/` — one file per design decision: what we chose, what the paper
  did, why we deviated
- `journal.md` — dated log; every entry ends with one "interview takeaway"
- `results.md` — running eval numbers vs. paper baselines

Conventions: [[wikilinks]] between notes; every paper note cites section or
table numbers; every decision note links the paper note it deviates from.

First task for Claude Code: read the PDF and populate `paper/` (see
KICKOFF_PROMPT.md).
