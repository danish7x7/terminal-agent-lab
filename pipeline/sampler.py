"""Compositional sampler: draw one value per axis into a task signature.

Deterministic given a seed. Axis shapes (decision 003):
  - flat:      `values: [...]`                sampled uniformly
  - weighted:  `weighted: {value: weight}`    normalized, then sampled
  - per_domain:`per_domain: {domain: [...]}`  indexed by the drawn `domain`
  - a per_domain axis may add `sample: {min, max}` to draw a *set* of values

Axes are resolved in file order, so domain-conditioned axes see `domain`.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

DEFAULT_AXES_PATH = Path(__file__).parent / "axes.yaml"


@dataclass
class Signature:
    seed: int
    domain: str
    skill_type: str
    primitive_skills: list[str]
    persona: str
    language: str
    task_complexity: str
    command_complexity: str
    fixture: str
    verifier: str

    def to_dict(self) -> dict:
        return asdict(self)


def load_axes(path: str | Path | None = None) -> dict:
    data = yaml.safe_load(Path(path or DEFAULT_AXES_PATH).read_text())
    if not isinstance(data, dict) or "axes" not in data:
        raise ValueError("axes file must be a mapping with a top-level `axes` key")
    return data["axes"]


def _sample_flat(spec: dict, rng: random.Random) -> str:
    values = spec.get("values")
    if not values:
        raise ValueError("flat axis needs a non-empty `values` list")
    return rng.choice(values)


def _sample_weighted(spec: dict, rng: random.Random) -> str:
    weighted = spec["weighted"]
    values = list(weighted.keys())
    weights = list(weighted.values())
    if any(w < 0 for w in weights) or sum(weights) <= 0:
        raise ValueError("weighted axis needs positive weights summing > 0")
    return rng.choices(values, weights=weights, k=1)[0]


def _sample_per_domain(spec: dict, domain: str, rng: random.Random):
    options = spec["per_domain"].get(domain)
    if not options:
        raise ValueError(f"per_domain axis has no options for domain {domain!r}")
    sample = spec.get("sample")
    if sample is None:
        return rng.choice(options)
    lo, hi = sample["min"], sample["max"]
    count = min(rng.randint(lo, hi), len(options))
    return rng.sample(options, count)


def _resolve_axis(name: str, spec: dict, drawn: dict, rng: random.Random):
    if "values" in spec:
        return _sample_flat(spec, rng)
    if "weighted" in spec:
        return _sample_weighted(spec, rng)
    if "per_domain" in spec:
        if "domain" not in drawn:
            raise ValueError(f"per_domain axis {name!r} resolved before `domain`")
        return _sample_per_domain(spec, drawn["domain"], rng)
    raise ValueError(f"axis {name!r} has no recognised shape (values/weighted/per_domain)")


def sample_signature(seed: int, axes: dict | None = None) -> Signature:
    """Draw one value per axis deterministically from `seed`."""
    if axes is None:
        axes = load_axes()
    rng = random.Random(seed)
    drawn: dict = {}
    for name, spec in axes.items():
        drawn[name] = _resolve_axis(name, spec, drawn, rng)
    return Signature(seed=seed, **drawn)
