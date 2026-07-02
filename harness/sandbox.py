"""Docker container lifecycle for task sandboxes.

Containers always get resource limits and never mount the host filesystem
(CLAUDE.md rule). Files move in via `docker cp` only.
"""

from __future__ import annotations

import subprocess
import uuid


class SandboxError(RuntimeError):
    pass


def build_image(context_dir: str, tag: str, timeout: int = 600) -> str:
    """Build a task image from its directory; returns the tag."""
    proc = subprocess.run(
        ["docker", "build", "-q", "-t", tag, str(context_dir)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise SandboxError(f"docker build failed for {context_dir}:\n{proc.stderr}")
    return tag


class Sandbox:
    """A running container executing `sleep infinity`, used as an exec target."""

    def __init__(self, image: str, memory: str = "2g", cpus: float = 2.0, network: str = "none"):
        self.image = image
        self.memory = memory
        self.cpus = cpus
        self.network = network
        self.name = f"tal-{uuid.uuid4().hex[:12]}"
        self._running = False

    def start(self) -> "Sandbox":
        proc = subprocess.run(
            [
                "docker", "run", "-d", "--rm",
                "--name", self.name,
                "--memory", self.memory,
                "--cpus", str(self.cpus),
                "--network", self.network,
                self.image,
                "sleep", "infinity",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            raise SandboxError(f"docker run failed:\n{proc.stderr}")
        self._running = True
        return self

    def exec(self, command: str, timeout: int = 120) -> subprocess.CompletedProcess:
        """One-shot command in a fresh shell (no persistent state). For plumbing,
        not for agent commands — those go through shell.PersistentShell."""
        return subprocess.run(
            ["docker", "exec", self.name, "bash", "-c", command],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def copy_in(self, src: str, dst: str) -> None:
        proc = subprocess.run(
            ["docker", "cp", str(src), f"{self.name}:{dst}"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            raise SandboxError(f"docker cp failed:\n{proc.stderr}")

    def stop(self) -> None:
        if self._running:
            subprocess.run(
                ["docker", "rm", "-f", self.name],
                capture_output=True,
                text=True,
                timeout=60,
            )
            self._running = False

    def __enter__(self) -> "Sandbox":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()
