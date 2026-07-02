"""The agent loop: prompt -> command -> execute -> observation, until submit,
max_steps, or token budget."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.command_parser import parse_reply
from harness.config import RunConfig
from harness.prompts import SYSTEM_PROMPT, format_error, format_observation, format_task


@dataclass
class Step:
    reply: str
    command: str | None
    observation: str
    exit_code: int | None = None
    timed_out: bool = False
    format_error: str | None = None


@dataclass
class EpisodeResult:
    steps: list[Step] = field(default_factory=list)
    submitted: bool = False
    stop_reason: str = "max_steps"  # submitted | max_steps | token_budget
    input_tokens: int = 0
    output_tokens: int = 0


def _truncate(text: str, limit: int) -> tuple[str, bool]:
    """Keep head and tail; the middle of long output is the least informative."""
    if len(text) <= limit:
        return text, False
    head = text[: limit // 2]
    tail = text[-(limit // 2) :]
    return f"{head}\n... [{len(text) - limit} chars omitted] ...\n{tail}", True


def run_episode(llm, shell, instructions: str, cfg: RunConfig) -> EpisodeResult:
    result = EpisodeResult()
    messages: list[dict] = [{"role": "user", "content": format_task(instructions)}]

    for _ in range(cfg.max_steps):
        reply = llm.chat(SYSTEM_PROMPT, messages)
        result.input_tokens += reply.input_tokens
        result.output_tokens += reply.output_tokens
        messages.append({"role": "assistant", "content": reply.text})

        parsed = parse_reply(reply.text)
        if parsed.error:
            observation = format_error(parsed.error)
            result.steps.append(Step(reply.text, None, observation, format_error=parsed.error))
        elif parsed.submitted:
            result.steps.append(Step(reply.text, parsed.command, "(submitted)"))
            result.submitted = True
            result.stop_reason = "submitted"
            return result
        else:
            shell_result = shell.run(parsed.command)
            output, truncated = _truncate(shell_result.output, cfg.max_output_chars)
            observation = format_observation(
                output, shell_result.exit_code, truncated, shell_result.timed_out
            )
            result.steps.append(
                Step(
                    reply.text,
                    parsed.command,
                    observation,
                    exit_code=shell_result.exit_code,
                    timed_out=shell_result.timed_out,
                )
            )
        messages.append({"role": "user", "content": observation})

        if result.input_tokens + result.output_tokens > cfg.token_budget:
            result.stop_reason = "token_budget"
            return result

    result.stop_reason = "max_steps"
    return result
