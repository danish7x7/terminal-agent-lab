"""Compositional task pipeline: axes -> signature -> generated task dir.

See docs/notes/decisions/003-pipeline-design.md for the authoritative design.
"""

from pipeline.sampler import Signature, load_axes, sample_signature

__all__ = ["Signature", "load_axes", "sample_signature"]
