"""Persistent shell inside a sandbox container.

One long-lived `docker exec -i <container> bash` process; each command is
followed by a unique sentinel that carries the exit code. On timeout the shell
process is killed and restarted (container and its background processes
survive; shell-local state like cwd is lost and the agent is told so).
"""

from __future__ import annotations

import queue
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass

from harness.sandbox import Sandbox


@dataclass
class ShellResult:
    output: str
    exit_code: int | None
    timed_out: bool = False


class PersistentShell:
    def __init__(self, sandbox: Sandbox, timeout: int = 120):
        self.sandbox = sandbox
        self.timeout = timeout
        self._proc: subprocess.Popen | None = None
        self._lines: queue.Queue[str | None] = queue.Queue()
        self._start()

    def _start(self) -> None:
        self._lines = queue.Queue()
        self._proc = subprocess.Popen(
            ["docker", "exec", "-i", self.sandbox.name, "bash", "--norc", "--noprofile"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            bufsize=1,
        )
        threading.Thread(target=self._reader, args=(self._proc,), daemon=True).start()

    def _reader(self, proc: subprocess.Popen) -> None:
        for line in proc.stdout:
            self._lines.put(line)
        self._lines.put(None)  # EOF

    def _restart(self) -> None:
        if self._proc is not None:
            self._proc.kill()
            self._proc.wait()
        self._start()

    def run(self, command: str) -> ShellResult:
        if self._proc is None or self._proc.poll() is not None:
            self._restart()
        sentinel = f"__CMD_DONE_{uuid.uuid4().hex}__"
        assert self._proc is not None and self._proc.stdin is not None
        try:
            self._proc.stdin.write(f"{command}\nprintf '%s %s\\n' {sentinel} $?\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError):
            self._restart()
            return ShellResult(output="(shell had died and was restarted; command not run)", exit_code=None)

        deadline = time.monotonic() + self.timeout
        collected: list[str] = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._restart()
                return ShellResult(output="".join(collected), exit_code=None, timed_out=True)
            try:
                line = self._lines.get(timeout=remaining)
            except queue.Empty:
                self._restart()
                return ShellResult(output="".join(collected), exit_code=None, timed_out=True)
            if line is None:
                # Shell exited (e.g. the agent ran `exit`); restart for next turn.
                self._restart()
                return ShellResult(output="".join(collected), exit_code=None)
            if line.startswith(sentinel):
                try:
                    exit_code = int(line.split()[1])
                except (IndexError, ValueError):
                    exit_code = None
                return ShellResult(output="".join(collected), exit_code=exit_code)
            collected.append(line)

    def close(self) -> None:
        if self._proc is not None:
            self._proc.kill()
            self._proc.wait()
            self._proc = None
