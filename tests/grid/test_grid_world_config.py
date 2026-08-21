import json

import pytest

from src_grid.core.world_config import WorldConfig, DEFAULTS, sanitize_filename


@pytest.fixture
def tmp_config_path(tmp_path):
    return tmp_path / "grid_world_config.json"


def test_defaults_used_when_no_file_exists(tmp_config_path):
    config = WorldConfig(path=tmp_config_path)

    for key, value in DEFAULTS.items():
        assert config.get(key) == value


def test_load_picks_up_existing_file(tmp_config_path):
    tmp_config_path.write_text(json.dumps({"width": 99}), encoding="utf-8")

    config = WorldConfig(path=tmp_config_path)

    assert config.get("width") == 99
    # untouched keys keep their default
    assert config.get("height") == DEFAULTS["height"]


def test_load_ignores_malformed_file(tmp_config_path):
    tmp_config_path.write_text("not valid json", encoding="utf-8")

    config = WorldConfig(path=tmp_config_path)

    assert config.get("width") == DEFAULTS["width"]


def test_save_writes_current_data(tmp_config_path):
    config = WorldConfig(path=tmp_config_path)
    config.data["organism_count"] = 5
    config.save()

    on_disk = json.loads(tmp_config_path.read_text(encoding="utf-8"))
    assert on_disk["organism_count"] == 5


def test_load_from_file_adopts_and_persists_as_the_single_canonical_file(tmp_path, tmp_config_path):
    other_path = tmp_path / "preset.json"
    other_path.write_text(json.dumps({"organism_count": 77, "food_count": 111}), encoding="utf-8")

    config = WorldConfig(path=tmp_config_path)
    config.load_from_file(other_path)

    assert config.get("organism_count") == 77
    assert config.get("food_count") == 111

    assert tmp_config_path.exists()
    on_disk = json.loads(tmp_config_path.read_text(encoding="utf-8"))
    assert on_disk["organism_count"] == 77


@pytest.mark.parametrize("raw,expected", [
    ("My World", "My World"),
    ("weird/na\\me:*?\"<>|end", "weird_na_me_______end"),
    ("   padded   ", "padded"),
    ("", "grid_world"),
    ("   ", "grid_world"),
])
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


def test_save_as_writes_named_file_with_name_field(tmp_path, tmp_config_path):
    config = WorldConfig(path=tmp_config_path)
    config.data["organism_count"] = 12

    target = config.save_as(tmp_path, "My Cool World")

    assert target == tmp_path / "My Cool World.json"
    assert target.exists()

    on_disk = json.loads(target.read_text(encoding="utf-8"))
    assert on_disk["name"] == "My Cool World"
    assert on_disk["organism_count"] == 12


def test_save_as_makes_the_new_file_the_active_one(tmp_path, tmp_config_path):
    config = WorldConfig(path=tmp_config_path)
    original_path = config.path

    target = config.save_as(tmp_path, "Renamed")

    assert config.path == target
    assert config.path != original_path
