"""Agent-loop tests with a scripted fake LLM and fake shell (no Docker, no API)."""

from dataclasses import dataclass, field

from harness.command_parser import SUBMIT_COMMAND
from harness.config import RunConfig
from harness.episode import run_episode
from harness.llm import LLMReply
from harness.shell import ShellResult


@dataclass
class FakeLLM:
    replies: list[str]
    calls: int = 0

    def chat(self, system, messages):
        reply = self.replies[min(self.calls, len(self.replies) - 1)]
        self.calls += 1
        return LLMReply(reply, input_tokens=100, output_tokens=20)


@dataclass
class FakeShell:
    commands: list[str] = field(default_factory=list)
    output: str = "ok\n"

    def run(self, command):
        self.commands.append(command)
        return ShellResult(output=self.output, exit_code=0)


CFG = RunConfig(max_steps=5)


def block(cmd: str) -> str:
    return f"```bash\n{cmd}\n```"


def test_commands_then_submit():
    llm = FakeLLM([block("ls"), block("touch /app/x"), block(SUBMIT_COMMAND)])
    shell = FakeShell()
    result = run_episode(llm, shell, "make x", CFG)
    assert result.submitted
    assert result.stop_reason == "submitted"
    assert shell.commands == ["ls", "touch /app/x"]  # submit is not executed
    assert len(result.steps) == 3


def test_max_steps_stops_loop():
    llm = FakeLLM([block("echo again")])
    shell = FakeShell()
    result = run_episode(llm, shell, "loop forever", CFG)
    assert not result.submitted
    assert result.stop_reason == "max_steps"
    assert len(result.steps) == CFG.max_steps


def test_format_error_feeds_back_and_loop_recovers():
    llm = FakeLLM(["no code block here", block(SUBMIT_COMMAND)])
    shell = FakeShell()
    result = run_episode(llm, shell, "task", CFG)
    assert result.steps[0].format_error is not None
    assert "FORMAT ERROR" in result.steps[0].observation
    assert result.submitted
    assert shell.commands == []


def test_mixed_submit_feeds_back_and_loop_recovers():
    llm = FakeLLM(
        [
            block(f"mkdir -p /output\n{SUBMIT_COMMAND}"),  # mixed: rejected
            block("mkdir -p /output"),
            block(SUBMIT_COMMAND),
        ]
    )
    shell = FakeShell()
    result = run_episode(llm, shell, "task", CFG)
    assert result.steps[0].format_error == "mixed_command_and_submit"
    assert "separate messages" in result.steps[0].observation
    assert shell.commands == ["mkdir -p /output"]  # nothing from the mixed reply ran
    assert result.submitted


def test_token_budget_stops_loop():
    llm = FakeLLM([block("echo hi")])
    result = run_episode(llm, FakeShell(), "task", RunConfig(max_steps=50, token_budget=300))
    assert result.stop_reason == "token_budget"
    assert len(result.steps) < 50


def test_long_output_is_truncated_in_observation():
    llm = FakeLLM([block("cat big"), block(SUBMIT_COMMAND)])
    shell = FakeShell(output="x" * 50_000)
    result = run_episode(llm, shell, "task", CFG)
    assert "chars omitted" in result.steps[0].observation
    assert len(result.steps[0].observation) < 12_000
