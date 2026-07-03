# Generator exemplars

One hand-written worked example per verifier kind, used as few-shot context in
the generator prompt (decision 003 §3). Each `*.json` is exactly the object the
generator must emit for one task:

```json
{
  "task_md":       "...",              // instructions; never mentions tests/grading
  "dockerfile":    "FROM ...",         // per-domain base; all downloads at build time
  "tests":         {"test_*.py": ...}, // fails on fresh container, passes when solved
  "solution_md":   "...",              // RUNNABLE reference solution (Gate B' executes it)
  "fixture_files": {"path": "..."}     // build-context files the Dockerfile COPYs
}
```

These double as fixtures for the gate/generator tests once those land. They are
authored to *pass their own gates* by construction:

- Gate B (not pre-solved): the fresh container fails the test.
- Gate B′ (test solvable): running `solution_md`'s commands makes it pass.
- `task.md` never names the test files or the grading rule.

Files: `exact_text.json`, `metric_threshold.json`.
