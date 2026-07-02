"""System prompt and observation templates (mini-SWE-agent style)."""

from __future__ import annotations

from harness.command_parser import MIXED_SUBMIT, MULTIPLE_BLOCKS, NO_BLOCK, SUBMIT_COMMAND

SYSTEM_PROMPT = f"""You are a terminal agent solving a task inside a Linux container.

Rules:
- Reply with EXACTLY ONE bash command per turn, inside a single fenced code block:

```bash
your command here
```

- The shell is persistent: working directory, environment variables, and
  background processes carry over between turns.
- After each command you will see its combined stdout/stderr and exit code.
- Long output is truncated. Inspect files with head/tail/grep instead of
  dumping them whole.
- Never use interactive programs (vim, nano, less, top). Use non-interactive
  flags (e.g. `sed -i`, `apt-get -y`).
- When you are confident the task is fully complete, submit by replying with
  exactly this command and nothing else:

```bash
{SUBMIT_COMMAND}
```

- NEVER combine work commands and the submit command in the same reply. Run
  your commands first (one reply each), then submit in a separate, final reply.
"""


def format_task(instructions: str) -> str:
    return f"Your task:\n\n{instructions.strip()}\n\nBegin now. Remember: one bash command per reply."


def format_observation(output: str, exit_code: int | None, truncated: bool, timed_out: bool) -> str:
    parts = []
    if timed_out:
        parts.append(
            "COMMAND TIMED OUT and the shell was restarted "
            "(unsaved shell state such as cwd and env vars was lost)."
        )
    if truncated:
        parts.append("(output truncated)")
    parts.append(f"Output:\n{output if output.strip() else '(no output)'}")
    parts.append(f"Exit code: {exit_code if exit_code is not None else 'unknown'}")
    return "\n".join(parts)


_FORMAT_ERRORS = {
    NO_BLOCK: "Your reply contained no fenced code block.",
    MULTIPLE_BLOCKS: "Your reply contained more than one fenced code block.",
    MIXED_SUBMIT: (
        "Your reply mixed commands with the submit command. Nothing was "
        "executed and nothing was submitted. Run commands and submit in "
        "separate messages: send your command now, then submit "
        f"(`{SUBMIT_COMMAND}` alone) in a later reply."
    ),
}


def format_error(error: str) -> str:
    reason = _FORMAT_ERRORS.get(error, error)
    return (
        f"FORMAT ERROR: {reason} "
        "Reply with exactly one bash command in a single ```bash fenced block."
    )
