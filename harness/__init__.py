"""Eval harness: LLM <-> persistent shell in a Docker container.

See docs/notes/paper/harness.md for the paper-derived contract this implements.
"""

from harness.runner import run_task

__all__ = ["run_task"]
