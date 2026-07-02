"""Run k rollouts of a task, compute pass@k, write JSONL rows to evals/results/."""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

from dataclasses import asdict

from harness.config import RunConfig
from harness.episode import EpisodeResult, run_episode
from harness.llm import make_client
from harness.sandbox import Sandbox, build_image
from harness.shell import PersistentShell
from harness.verifier import run_verifier


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k).

    n rollouts, c successes. The paper reports mean pass@k across tasks but
    never states the estimator; see docs/notes/paper/harness.md.
    """
    if k > n:
        raise ValueError(f"k={k} > n={n}")
    if c == 0:
        return 0.0
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def summarize(task_id: str, model: str, rewards: list[float]) -> dict:
    n = len(rewards)
    c = sum(1 for r in rewards if r == 1.0)  # pass <=> all verifier tests green
    ks = sorted({k for k in (1, 4, 8, n) if k <= n})
    return {
        "task_id": task_id,
        "model": model,
        "n": n,
        "successes": c,
        "mean_reward": sum(rewards) / n if n else 0.0,
        "pass_at_k": {str(k): pass_at_k(n, c, k) for k in ks},
    }


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row) + "\n")


def _write_transcript(path: Path, meta: dict, episode: EpisodeResult) -> None:
    """Full per-step record (model replies + observations) as a sidecar JSON,
    so failed rollouts can be investigated after the fact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                **meta,
                "stop_reason": episode.stop_reason,
                "submitted": episode.submitted,
                "input_tokens": episode.input_tokens,
                "output_tokens": episode.output_tokens,
                "steps": [asdict(step) for step in episode.steps],
            },
            indent=2,
        )
    )


def run_task(task_dir: str | Path, cfg: RunConfig, out_dir: str | Path = "evals/results") -> dict:
    task_dir = Path(task_dir)
    task_id = task_dir.name
    instructions = (task_dir / "task.md").read_text()
    tests_dir = task_dir / "tests"

    image = build_image(task_dir, f"tal-task-{task_id}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    model_slug = cfg.model.replace("/", "_").replace(":", "_")
    run_stem = f"{task_id}__{model_slug}__{stamp}"
    out_path = Path(out_dir) / f"{run_stem}.jsonl"
    transcripts_dir = Path(out_dir) / "transcripts"

    rewards: list[float] = []
    for rollout in range(cfg.k):
        started = time.monotonic()
        llm = make_client(cfg.model, cfg.temperature, cfg.max_reply_tokens)
        with Sandbox(image, cfg.container()) as sandbox:
            shell = PersistentShell(sandbox, timeout=cfg.cmd_timeout)
            try:
                episode = run_episode(llm, shell, instructions, cfg)
                verdict = run_verifier(sandbox, str(tests_dir))
            finally:
                shell.close()
        rewards.append(verdict.reward)
        transcript_path = transcripts_dir / f"{run_stem}__r{rollout}.json"
        _write_transcript(
            transcript_path,
            {"task_id": task_id, "model": cfg.model, "rollout": rollout, "reward": verdict.reward},
            episode,
        )
        _append_jsonl(
            out_path,
            {
                "task_id": task_id,
                "model": cfg.model,
                "rollout": rollout,
                "transcript": str(transcript_path),
                "reward": verdict.reward,
                "passed": verdict.reward == 1.0,
                "tests_passed": verdict.passed,
                "tests_failed": verdict.failed + verdict.errors,
                "steps": len(episode.steps),
                "stop_reason": episode.stop_reason,
                "submitted": episode.submitted,
                "input_tokens": episode.input_tokens,
                "output_tokens": episode.output_tokens,
                "duration_s": round(time.monotonic() - started, 1),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    summary = summarize(task_id, cfg.model, rewards)
    summary["results_file"] = str(out_path)
    return summary
