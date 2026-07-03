"""Sampler tests: determinism, axis shapes, domain conditioning."""

import pytest

from pipeline.sampler import Signature, load_axes, sample_signature

AXES = load_axes()  # the real pipeline/axes.yaml


def test_real_axes_file_loads_and_has_nine_axes():
    assert set(AXES) == {
        "domain", "task_complexity", "command_complexity", "fixture",
        "verifier", "language", "skill_type", "primitive_skills", "persona",
    }


def test_same_seed_is_deterministic():
    a = sample_signature(42, AXES)
    b = sample_signature(42, AXES)
    assert a == b


def test_different_seeds_differ_somewhere():
    sigs = [sample_signature(s, AXES) for s in range(20)]
    # not all identical across 20 seeds
    assert len({s.domain for s in sigs}) > 1


def test_signature_fields_respect_reduced_scope():
    for s in range(30):
        sig = sample_signature(s, AXES)
        assert sig.fixture == "text_only"
        assert sig.verifier in {"exact_text", "metric_threshold"}
        assert sig.task_complexity in {"short", "moderate", "complex", "intricate"}


def test_per_domain_axes_match_drawn_domain():
    for s in range(50):
        sig = sample_signature(s, AXES)
        assert sig.skill_type in AXES["skill_type"]["per_domain"][sig.domain]
        assert sig.persona in AXES["persona"]["per_domain"][sig.domain]
        pool = AXES["primitive_skills"]["per_domain"][sig.domain]
        assert set(sig.primitive_skills).issubset(pool)


def test_primitive_skills_count_in_range_and_unique():
    for s in range(50):
        sig = sample_signature(s, AXES)
        assert 3 <= len(sig.primitive_skills) <= 5
        assert len(set(sig.primitive_skills)) == len(sig.primitive_skills)


def test_weighted_axis_favors_high_weight_value():
    counts = {}
    for s in range(400):
        lang = sample_signature(s, AXES).language
        counts[lang] = counts.get(lang, 0) + 1
    # python has the highest weight (0.40); rust/multi_language the lowest
    assert counts.get("python", 0) > counts.get("rust", 0)


def test_signature_to_dict_round_trips():
    sig = sample_signature(7, AXES)
    d = sig.to_dict()
    assert d["seed"] == 7
    assert Signature(**d) == sig


def test_flat_axis_needs_values():
    with pytest.raises(ValueError):
        sample_signature(0, {"domain": {}})


def test_per_domain_before_domain_raises():
    axes = {"skill_type": {"per_domain": {"x": ["a"]}}}
    with pytest.raises(ValueError, match="before"):
        sample_signature(0, axes)


def test_unknown_axis_shape_raises():
    axes = {"domain": {"values": ["x"]}, "weird": {"mystery": 1}}
    with pytest.raises(ValueError, match="recognised shape"):
        sample_signature(0, axes)
