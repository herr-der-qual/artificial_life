import json

import pytest

from core.world_config import WorldConfig, DEFAULTS, sanitize_filename


@pytest.fixture
def tmp_config_path(tmp_path):
    return tmp_path / "world_config.json"


def test_defaults_used_when_no_file_exists(tmp_config_path):
    config = WorldConfig(path=tmp_config_path)

    for key, value in DEFAULTS.items():
        assert config.get(key) == value


def test_load_picks_up_existing_file(tmp_config_path):
    tmp_config_path.write_text(json.dumps({"initial_organism_count": 99}), encoding="utf-8")

    config = WorldConfig(path=tmp_config_path)

    assert config.get("initial_organism_count") == 99
    # untouched keys keep their default
    assert config.get("initial_substance_count") == DEFAULTS["initial_substance_count"]


def test_load_ignores_malformed_file(tmp_config_path):
    tmp_config_path.write_text("not valid json", encoding="utf-8")

    config = WorldConfig(path=tmp_config_path)

    assert config.get("initial_organism_count") == DEFAULTS["initial_organism_count"]


def test_save_writes_current_data(tmp_config_path):
    config = WorldConfig(path=tmp_config_path)
    config.data["initial_organism_count"] = 5
    config.save()

    on_disk = json.loads(tmp_config_path.read_text(encoding="utf-8"))
    assert on_disk["initial_organism_count"] == 5


def test_load_from_file_adopts_and_persists_as_the_single_canonical_file(tmp_path, tmp_config_path):
    other_path = tmp_path / "preset.json"
    other_path.write_text(json.dumps({"initial_organism_count": 77, "substance_spawn_bound": 111.0}), encoding="utf-8")

    config = WorldConfig(path=tmp_config_path)
    config.load_from_file(other_path)

    # in-memory state adopted the preset
    assert config.get("initial_organism_count") == 77
    assert config.get("substance_spawn_bound") == 111.0

    # and it was persisted into the ONE canonical file, not a second one
    assert tmp_config_path.exists()
    on_disk = json.loads(tmp_config_path.read_text(encoding="utf-8"))
    assert on_disk["initial_organism_count"] == 77


def test_load_from_file_does_not_create_a_second_file(tmp_path, tmp_config_path):
    other_path = tmp_path / "preset.json"
    other_path.write_text(json.dumps({"initial_organism_count": 3}), encoding="utf-8")

    config = WorldConfig(path=tmp_config_path)
    config.load_from_file(other_path)

    files_in_tmp_path = {p.name for p in tmp_path.glob("*.json")}
    assert files_in_tmp_path == {"preset.json", "world_config.json"}


@pytest.mark.parametrize("raw,expected", [
    ("My World", "My World"),
    ("weird/na\\me:*?\"<>|end", "weird_na_me_______end"),
    ("   padded   ", "padded"),
    ("", "world"),
    ("   ", "world"),
])
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


def test_save_as_writes_named_file_with_name_field(tmp_path, tmp_config_path):
    config = WorldConfig(path=tmp_config_path)
    config.data["initial_organism_count"] = 12

    target = config.save_as(tmp_path, "My Cool World")

    assert target == tmp_path / "My Cool World.json"
    assert target.exists()

    on_disk = json.loads(target.read_text(encoding="utf-8"))
    assert on_disk["name"] == "My Cool World"
    assert on_disk["initial_organism_count"] == 12


def test_save_as_sanitizes_unsafe_characters_in_filename(tmp_path, tmp_config_path):
    config = WorldConfig(path=tmp_config_path)

    target = config.save_as(tmp_path, "weird/na\\me")

    assert target.name == "weird_na_me.json"
    assert target.exists()


def test_save_as_makes_the_new_file_the_active_one(tmp_path, tmp_config_path):
    config = WorldConfig(path=tmp_config_path)
    original_path = config.path

    target = config.save_as(tmp_path, "Renamed")

    assert config.path == target
    assert config.path != original_path

    # a plain save() now goes to the new location, not the old canonical one
    config.data["initial_organism_count"] = 42
    config.save()
    on_disk = json.loads(target.read_text(encoding="utf-8"))
    assert on_disk["initial_organism_count"] == 42
