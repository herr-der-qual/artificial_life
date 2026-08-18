import json

from core.settings import Settings, DEFAULTS


def test_defaults_when_no_file_exists(tmp_path):
    settings = Settings(path=tmp_path / "settings.json")
    for key, value in DEFAULTS.items():
        assert settings.get(key) == value


def test_set_does_not_write_until_flushed(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(path=path)

    settings.set("step_n", 42)

    assert not path.exists()
    assert settings.get("step_n") == 42


def test_save_writes_current_data(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(path=path)

    settings.set("step_n", 42)
    settings.save()

    with open(path) as f:
        data = json.load(f)
    assert data["step_n"] == 42


def test_maybe_flush_only_writes_when_dirty(tmp_path):
    path = tmp_path / "settings.json"
    settings = Settings(path=path)

    settings.maybe_flush()
    assert not path.exists()

    settings.set("paused", True)
    settings._last_flush = 0  # force the debounce window to have elapsed
    settings.maybe_flush()
    assert path.exists()


def test_loading_restores_previously_saved_values(tmp_path):
    path = tmp_path / "settings.json"
    first = Settings(path=path)
    first.set("target_fps", "infinite")
    first.set("paused", True)
    first.set("step_n", 7)
    first.save()

    second = Settings(path=path)
    assert second.get("target_fps") == "infinite"
    assert second.get("paused") is True
    assert second.get("step_n") == 7


def test_unknown_keys_in_file_are_ignored(tmp_path):
    path = tmp_path / "settings.json"
    with open(path, "w") as f:
        json.dump({"step_n": 3, "totally_made_up": "value"}, f)

    settings = Settings(path=path)
    assert settings.get("step_n") == 3
    assert "totally_made_up" not in settings.data


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("not valid json {{{")

    settings = Settings(path=path)
    assert settings.get("target_fps") == DEFAULTS["target_fps"]
