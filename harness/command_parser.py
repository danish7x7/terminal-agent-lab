"""Extract the single bash command from a model reply.

Protocol (mini-SWE-agent style, see decision 002): the model must reply with
exactly one fenced code block containing one bash command; it submits by
replying with a block containing ONLY the SUBMIT_COMMAND. Mixing commands and
the submit marker in one reply is a format error — the loop feeds the error
back so the model can run the commands and submit separately.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

SUBMIT_COMMAND = "echo COMPLETE_TASK_AND_SUBMIT"

_CODE_BLOCK_RE = re.compile(r"```(?:bash|sh|shell)?[ \t]*\n(.*?)```", re.DOTALL)

NO_BLOCK = "no_code_block"
MULTIPLE_BLOCKS = "multiple_code_blocks"
MIXED_SUBMIT = "mixed_command_and_submit"


@dataclass
class ParsedReply:
    command: str | None
    submitted: bool = False
    error: str | None = None


def _is_submit_only(block: str) -> bool:
    return block.strip() == SUBMIT_COMMAND


def _contains_submit_line(block: str) -> bool:
    return any(line.strip() == SUBMIT_COMMAND for line in block.splitlines())


def parse_reply(text: str) -> ParsedReply:
    blocks = [b.strip() for b in _CODE_BLOCK_RE.findall(text)]
    blocks = [b for b in blocks if b]
    if not blocks:
        return ParsedReply(None, error=NO_BLOCK)
    if len(blocks) == 1:
        block = blocks[0]
        if _is_submit_only(block):
            return ParsedReply(block, submitted=True)
        if _contains_submit_line(block):
            # Commands and the submit marker in one block: refuse rather than
            # guess which half the model meant (this silently ate rollouts
            # before decision 002 rev 2).
            return ParsedReply(None, error=MIXED_SUBMIT)
        return ParsedReply(block)
    if any(_contains_submit_line(b) for b in blocks):
        return ParsedReply(None, error=MIXED_SUBMIT)
    return ParsedReply(None, error=MULTIPLE_BLOCKS)
