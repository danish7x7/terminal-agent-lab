"""Extract the single bash command from a model reply.

Protocol (mini-SWE-agent style, see decision 002): the model must reply with
exactly one fenced code block containing one bash command; it submits by
running the exact SUBMIT_COMMAND.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

SUBMIT_COMMAND = "echo COMPLETE_TASK_AND_SUBMIT"

_CODE_BLOCK_RE = re.compile(r"```(?:bash|sh|shell)?[ \t]*\n(.*?)```", re.DOTALL)

NO_BLOCK = "no_code_block"
MULTIPLE_BLOCKS = "multiple_code_blocks"


@dataclass
class ParsedReply:
    command: str | None
    submitted: bool = False
    error: str | None = None


def parse_reply(text: str) -> ParsedReply:
    blocks = [b.strip() for b in _CODE_BLOCK_RE.findall(text)]
    blocks = [b for b in blocks if b]
    if not blocks:
        return ParsedReply(None, error=NO_BLOCK)
    if len(blocks) > 1:
        return ParsedReply(None, error=MULTIPLE_BLOCKS)
    command = blocks[0]
    if command.splitlines()[0].strip() == SUBMIT_COMMAND:
        return ParsedReply(command, submitted=True)
    return ParsedReply(command)
