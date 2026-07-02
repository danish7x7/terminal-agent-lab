"""Verifier tests; the container-based ones require Docker (auto-skipped otherwise)."""

from pathlib import Path

import pytest

from harness.sandbox import Sandbox, build_image
from harness.verifier import parse_pytest_summary, run_verifier

TASKS = Path(__file__).parent.parent / "tasks"


def test_parse_pytest_summary_unit():
    assert parse_pytest_summary("2 failed, 3 passed in 0.5s") == (3, 2, 0)
    assert parse_pytest_summary("1 error in 0.1s") == (0, 0, 1)
    assert parse_pytest_summary("garbage") == (0, 0, 0)


docker = pytest.mark.docker


@pytest.fixture(scope="module")
def hello_image():
    return build_image(TASKS / "toy-hello", "tal-task-toy-hello")


@docker
def test_reward_is_pass_fraction(hello_image, tmp_path):
    (tmp_path / "test_mixed.py").write_text(
        "def test_yes():\n    assert True\n\ndef test_no():\n    assert False\n"
    )
    with Sandbox(hello_image) as sandbox:
        result = run_verifier(sandbox, str(tmp_path))
    assert result.reward == 0.5
    assert (result.passed, result.failed) == (1, 1)


@docker
def test_solved_toy_hello_gets_full_reward(hello_image):
    with Sandbox(hello_image) as sandbox:
        sandbox.exec("printf 'Hello, terminal agent!\\n' > /app/greeting.txt")
        result = run_verifier(sandbox, str(TASKS / "toy-hello" / "tests"))
    assert result.reward == 1.0


@docker
def test_unsolved_toy_hello_gets_zero(hello_image):
    with Sandbox(hello_image) as sandbox:
        result = run_verifier(sandbox, str(TASKS / "toy-hello" / "tests"))
    assert result.reward == 0.0
