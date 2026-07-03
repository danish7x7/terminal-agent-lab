"""Per-domain base images (decision 003 flag 7).

Kept minimal and uniform for now — one Python base with coreutils — so per-task
builds only add task-specific deps. Split per domain later if a domain needs
heavier standing tooling (e.g. sqlite for data_querying); the generator prompt
already tells the model what the base provides so it won't re-install it.
"""

from __future__ import annotations

_DEFAULT = (
    "python:3.11-slim",
    "Debian slim with python3, pip, and standard coreutils/bash. "
    "No compilers or extra language runtimes unless the Dockerfile adds them.",
)

# domain -> (image, description of what is already installed)
BASE_IMAGES: dict[str, tuple[str, str]] = {}


def base_image_for(domain: str) -> tuple[str, str]:
    return BASE_IMAGES.get(domain, _DEFAULT)
