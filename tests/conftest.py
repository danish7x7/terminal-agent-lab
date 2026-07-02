import functools
import shutil
import subprocess

import pytest


@functools.cache
def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return (
            subprocess.run(
                ["docker", "info"], capture_output=True, timeout=20
            ).returncode
            == 0
        )
    except (subprocess.TimeoutExpired, OSError):
        return False


def pytest_collection_modifyitems(config, items):
    if docker_available():
        return
    skip = pytest.mark.skip(reason="Docker daemon not available")
    for item in items:
        if "docker" in item.keywords:
            item.add_marker(skip)
