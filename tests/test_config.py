import pytest

from harness.config import RunConfig, load_config


def test_defaults_match_spec():
    cfg = load_config()
    assert cfg.max_steps == 30
    assert cfg.cmd_timeout == 120  # paper Table 13
    assert cfg.k == 4


def test_yaml_values_load(tmp_path):
    path = tmp_path / "cfg.yaml"
    path.write_text("model: some/model\nmax_steps: 5\n")
    cfg = load_config(path)
    assert cfg.model == "some/model"
    assert cfg.max_steps == 5
    assert cfg.cmd_timeout == RunConfig.cmd_timeout  # untouched default


def test_overrides_beat_file_and_none_is_ignored(tmp_path):
    path = tmp_path / "cfg.yaml"
    path.write_text("model: file-model\nk: 2\n")
    cfg = load_config(path, overrides={"model": "cli-model", "k": None})
    assert cfg.model == "cli-model"
    assert cfg.k == 2


def test_unknown_key_raises(tmp_path):
    path = tmp_path / "cfg.yaml"
    path.write_text("max_stepz: 5\n")
    with pytest.raises(ValueError, match="max_stepz"):
        load_config(path)
