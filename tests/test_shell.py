"""Persistent-shell integration tests. Require Docker (auto-skipped otherwise)."""

import pytest

from harness.sandbox import Sandbox
from harness.shell import PersistentShell

pytestmark = pytest.mark.docker

IMAGE = "python:3.11-slim"


@pytest.fixture
def shell():
    with Sandbox(IMAGE, network="none") as sandbox:
        sh = PersistentShell(sandbox, timeout=10)
        yield sh
        sh.close()


def test_state_persists_across_commands(shell):
    shell.run("cd /tmp && export MARKER=hello")
    result = shell.run("echo $MARKER $(pwd)")
    assert result.output.strip() == "hello /tmp"
    assert result.exit_code == 0


def test_exit_code_reported(shell):
    assert shell.run("true").exit_code == 0
    assert shell.run("false").exit_code == 1


def test_stderr_is_captured(shell):
    result = shell.run("ls /definitely-not-a-real-path")
    assert "No such file" in result.output
    assert result.exit_code != 0


def test_timeout_kills_and_shell_recovers():
    with Sandbox(IMAGE, network="none") as sandbox:
        sh = PersistentShell(sandbox, timeout=2)
        try:
            result = sh.run("sleep 30")
            assert result.timed_out
            assert result.exit_code is None
            follow_up = sh.run("echo recovered")
            assert follow_up.output.strip() == "recovered"
            assert not follow_up.timed_out
        finally:
            sh.close()


def test_agent_exit_command_does_not_wedge_the_harness(shell):
    shell.run("exit")
    result = shell.run("echo still-alive")
    assert "still-alive" in result.output
