"""CLI: uv run harness --task tasks/<id> --model <name> --k 4"""

from __future__ import annotations

import argparse
import json

from harness.config import load_config
from harness.runner import run_task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harness", description="Run a terminal-agent task eval.")
    parser.add_argument("--task", required=True, help="task directory, e.g. tasks/toy-hello")
    parser.add_argument("--model", help="model name (claude-* -> Anthropic, else OpenRouter)")
    parser.add_argument("--k", type=int, help="rollouts per task")
    parser.add_argument("--max-steps", type=int, dest="max_steps")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--config", help="YAML config path (default: harness/default.yaml)")
    parser.add_argument("--out-dir", default="evals/results", help="JSONL output directory")
    args = parser.parse_args(argv)

    cfg = load_config(
        args.config,
        overrides={
            "model": args.model,
            "k": args.k,
            "max_steps": args.max_steps,
            "temperature": args.temperature,
        },
    )
    summary = run_task(args.task, cfg, out_dir=args.out_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
