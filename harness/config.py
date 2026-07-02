"""Run configuration: one YAML file, overridable from the CLI."""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).parent / "default.yaml"


@dataclass
class RunConfig:
    model: str = "claude-haiku-4-5-20251001"
    temperature: float = 1.0
    max_steps: int = 30            # paper uses 64 (Table 13); 30 per spec/decision 001
    cmd_timeout: int = 120         # seconds per command, matches paper Table 13
    max_reply_tokens: int = 4096   # model max_tokens per turn (paper: 16384)
    max_output_chars: int = 10_000  # observation truncation, see decision 002
    token_budget: int = 200_000    # input+output tokens across one episode
    k: int = 4                     # rollouts per task
    network: str = "none"          # docker --network for task containers
    memory: str = "2g"             # docker --memory
    cpus: float = 2.0              # docker --cpus


def load_config(path: str | Path | None = None, overrides: dict | None = None) -> RunConfig:
    """Load YAML config (defaults to harness/default.yaml), then apply CLI overrides.

    Override values that are None are ignored, so unset CLI flags fall through
    to the file values.
    """
    if path is None:
        path = DEFAULT_CONFIG_PATH
    data = yaml.safe_load(Path(path).read_text()) or {}
    if overrides:
        data.update({key: val for key, val in overrides.items() if val is not None})
    valid = {f.name for f in fields(RunConfig)}
    unknown = set(data) - valid
    if unknown:
        raise ValueError(f"unknown config keys: {sorted(unknown)}")
    return RunConfig(**data)
