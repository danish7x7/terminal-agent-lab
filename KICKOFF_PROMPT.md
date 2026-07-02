# Kickoff — do this once, in order

## 0. One-time setup (Windows)
1. Install WSL2 + Ubuntu: `wsl --install` in PowerShell (admin), reboot.
2. Install Docker Desktop, enable the WSL2 backend, verify inside Ubuntu:
   `docker run hello-world`.
3. Inside WSL2: install git, uv, and Claude Code (see
   https://docs.claude.com/en/docs/claude-code/overview for current install
   command — it changes; don't trust old blog posts).
4. Create the GitHub repo `terminal-agent-lab` (empty, private for now),
   clone it INSIDE the WSL2 filesystem (~/projects/, not /mnt/c/ — Docker
   and file-watching are much faster on the Linux side).

## 1. Seed the repo
1. Copy this starter kit into the repo root (CLAUDE.md, docs/, .claude/).
2. Create `paper/` and drop `2606_23321v1.pdf` into it.
3. `git add -A && git commit -m "chore: seed project scaffold" && git push`

## 2. First Claude Code session
`cd` into the repo, run `claude`, pick your model, then paste:

---

Read CLAUDE.md and docs/PROJECT_SPEC.md fully before doing anything.

Session goal — paper distillation, no application code yet:
1. Read paper/2606_23321v1.pdf. Populate docs/notes/paper/ with one note
   per concept as listed in docs/notes/README.md. Every claim cites a
   section or table number. For each note, add a final section "What we
   replicate vs. skip" based on the spec's phases and non-goals.
2. In docs/notes/paper/harness.md, extract everything needed to implement
   Phase 1: the agent loop shape, per-command timeout, max steps, how the
   verifier produces reward, and how pass@k is computed (paper §3.4, §4.1,
   Table 13).
3. Write docs/notes/decisions/001-scope.md summarizing our deviations from
   the paper (API models instead of RL-trained ones, ~100 tasks not 14.6k,
   no GRPO/DPPO) and the reasoning.
4. Propose — do not create yet — the Phase 1 file tree for harness/ with
   one line per file. Stop and wait for my approval.

Work in plan mode for step 4. Add a journal entry when done.

---

## 3. The loop with your reviewer chat
After each milestone, run /review-packet in Claude Code, paste the packet
into the reviewer chat (claude.ai), bring the feedback back into Claude Code
as "reviewer feedback: ...". Reviewer critiques; Claude Code implements.
