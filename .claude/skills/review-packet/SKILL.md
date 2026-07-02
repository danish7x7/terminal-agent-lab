---
name: review-packet
description: Prepare a review packet for the external reviewer (a separate
  Claude chat session). Use when the user says "prep review", "review packet",
  or finishes a phase milestone.
---

# Review Packet

Assemble a single markdown block the user will paste into their reviewer
chat session. Include, in this order:

1. **Context line**: project name, current phase from docs/PROJECT_SPEC.md,
   and what milestone this packet covers.
2. **What changed**: output of `git log --oneline -10` and
   `git diff --stat HEAD~N` for the relevant range.
3. **Key code**: the 1–3 most decision-heavy files or functions (full text,
   not summaries). Prefer the harness loop, sampler, or generator prompt.
4. **Results**: any new eval numbers from evals/results/ (pass@k, task build
   success rate), plus how they compare to the paper's reported numbers.
5. **Open questions**: 2–4 specific questions the user wants the reviewer to
   weigh in on (design tradeoffs, paper fidelity, what to build next).
6. **Journal delta**: the latest entry from docs/notes/journal.md.

Write the packet to `docs/review/packet-YYYY-MM-DD.md` AND print it in full
so the user can copy it. Keep it under ~400 lines; link file paths rather
than inlining anything that isn't decision-relevant.
