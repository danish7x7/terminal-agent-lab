"""Post-episode verification: copy the task's tests/ into the container fresh
(so the agent could not have tampered with them, paper SD.6) and run pytest.

Reward = fraction of tests passed, which is binary for single-test tasks and
supports graded verifiers (docs/notes/paper/verifiers.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from harness.sandbox import Sandbox

TESTS_DST = "/task_tests"

_COUNT_RE = {
    "passed": re.compile(r"(\d+) passed"),
    "failed": re.compile(r"(\d+) failed"),
    "errors": re.compile(r"(\d+) error"),
}


@dataclass
class VerifierResult:
    reward: float
    passed: int
    failed: int
    errors: int
    output: str


def parse_pytest_summary(output: str) -> tuple[int, int, int]:
    counts = {}
    for key, pattern in _COUNT_RE.items():
        match = pattern.search(output)
        counts[key] = int(match.group(1)) if match else 0
    return counts["passed"], counts["failed"], counts["errors"]


def run_verifier(sandbox: Sandbox, tests_dir: str, timeout: int = 300) -> VerifierResult:
    sandbox.exec(f"rm -rf {TESTS_DST} && mkdir -p {TESTS_DST}", timeout=30)
    sandbox.copy_in(f"{tests_dir}/.", f"{TESTS_DST}/")
    proc = sandbox.exec(
        f"cd {TESTS_DST} && python -m pytest -q --tb=line -p no:cacheprovider",
        timeout=timeout,
    )
    output = proc.stdout + proc.stderr
    passed, failed, errors = parse_pytest_summary(output)
    total = passed + failed + errors
    reward = passed / total if total else 0.0
    return VerifierResult(reward, passed, failed, errors, output)
