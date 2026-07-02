# Project: terminal-agent-lab

A scoped-down replication of the TMAX paper (arXiv:2606.23321) — a synthetic
data pipeline + eval harness for terminal agents. Portfolio project; goal is
depth of understanding and a demo-able artifact, NOT full-scale RL training.

## Source of truth
- The paper PDF lives at `paper/2606_23321v1.pdf`. Distilled notes live in
  `docs/notes/`. When implementing anything from the paper, check the notes
  first; if a detail is missing, read the relevant PDF section and ADD it to
  the notes before coding.
- The project plan and current phase live in `docs/PROJECT_SPEC.md`. Never
  start work outside the current phase without asking.

## Environment
- Windows host, all work happens inside WSL2 Ubuntu. Docker via Docker Desktop
  (WSL2 backend). Assume `docker` is available; never use `sudo docker`.
- Python 3.11+, uv for dependency management (`uv add`, `uv run`).
- No GPU locally. Model calls go through APIs (Anthropic / OpenRouter);
  API keys come from `.env` (never commit, never print).

## Layout
- `harness/` — agent loop: LLM ↔ persistent shell in a Docker container
- `pipeline/` — compositional task generator (axes → task → Dockerfile + tests)
- `tasks/` — generated task instances (one dir per task)
- `evals/` — pass@k runners and results (results as JSONL, plots in evals/plots)
- `docs/notes/` — Obsidian-style vault: paper notes, decisions, learnings
- `paper/` — the source PDF (read-only reference)

## Conventions
- Small, reviewed steps: propose a plan before multi-file changes.
- Every module gets a test; run `uv run pytest` before claiming done.
- Commit format: `feat|fix|docs|chore(scope): description`. Commit per
  logical unit, not per session.
- After completing any meaningful chunk, append a dated entry to
  `docs/notes/journal.md` with: what was built, why, and one thing learned
  (interview fodder). Use [[wikilinks]] to other notes.
- All containers get resource limits (`--memory`, `--cpus`) and timeouts.
  Never mount the host filesystem into task containers.

## What NOT to do
- No RL training code (GRPO/DPPO) — out of scope; concepts go in notes only.
- Don't generate more than 10 tasks per run without asking (API cost).
- Don't refactor the harness and pipeline in the same session.
