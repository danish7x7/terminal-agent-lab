"""Sandbox flag-wiring tests. No Docker needed — subprocess.run is stubbed so
we can assert on the exact `docker run` argv (decision 003 amendment 5)."""

import subprocess

from harness.config import RunConfig
from harness.sandbox import ContainerConfig, Sandbox


def _capture_run_argv(config):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="cid\n", stderr="")

    import harness.sandbox as sandbox_mod

    original = sandbox_mod.subprocess.run
    sandbox_mod.subprocess.run = fake_run
    try:
        Sandbox("img", config).start()
    finally:
        sandbox_mod.subprocess.run = original
    return captured["cmd"]


def _flag_value(cmd, flag):
    return cmd[cmd.index(flag) + 1]


def test_run_command_carries_all_four_resource_flags():
    cmd = _capture_run_argv(
        ContainerConfig(network="none", memory="512m", cpus=1.5, pids_limit=256)
    )
    assert _flag_value(cmd, "--network") == "none"
    assert _flag_value(cmd, "--memory") == "512m"
    assert _flag_value(cmd, "--cpus") == "1.5"
    assert _flag_value(cmd, "--pids-limit") == "256"


def test_run_command_has_no_host_bind_mount():
    cmd = _capture_run_argv(ContainerConfig())
    assert "-v" not in cmd
    assert "--mount" not in cmd
    assert not any(str(a).startswith("--volume") for a in cmd)


def test_defaults_include_pids_limit():
    cmd = _capture_run_argv(ContainerConfig())
    assert _flag_value(cmd, "--pids-limit") == "512"


def test_run_config_container_threads_all_flags():
    cc = RunConfig(network="bridge", memory="1g", cpus=3.0, pids_limit=128).container()
    assert cc == ContainerConfig(network="bridge", memory="1g", cpus=3.0, pids_limit=128)
