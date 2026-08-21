import json
import re
from pathlib import Path

WORLD_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "grid_world_config.json"
WORLD_CONFIGS_DIR = Path(__file__).resolve().parent.parent.parent / "grid_world_configs"

DEFAULTS = {
    "name": "Untitled Grid World",
    "width": 40,
    "height": 30,
    "food_count": 80,
    "organism_count": 20,
}

_UNSAFE_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def sanitize_filename(name: str) -> str:
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", name).strip()
    return cleaned or "grid_world"


class WorldConfig:
    """JSON-backed start/generation settings for a fresh grid World - the
    "how to create it" knobs (width, height, how much food/how many
    organisms to spawn). Deliberately separate from a live save (see
    core.world_save), which captures the actual running state instead of
    just the recipe used to start one. Mirrors core.world_config.WorldConfig
    from the pymunk system - same shape and behavior, kept as its own class
    (and its own on-disk file, grid_world_config.json, distinct from the
    pymunk system's world_config.json) so the two simulations never fight
    over the same config file. As with that one, the DEFAULTS live in code,
    and there's always exactly one canonical file on disk - never a
    separate "current" vs "default" pair."""

    def __init__(self, path: Path = WORLD_CONFIG_PATH):
        self.path = path
        self.data = dict(DEFAULTS)
        self.load()

    def load(self, path: Path = None):
        target = path or self.path

        if not target.exists():
            return

        try:
            with open(target, "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except (OSError, json.JSONDecodeError):
            return

        for key in DEFAULTS:
            if key in loaded:
                self.data[key] = loaded[key]

    def save(self, path: Path = None):
        target = path or self.path
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get(self, key):
        return self.data.get(key, DEFAULTS.get(key))

    def load_from_file(self, source_path):
        """Adopt another grid config file as the active one: read it, then
        persist it into the canonical grid_world_config.json."""
        self.load(Path(source_path))
        self.save()

    def save_as(self, directory, name: str) -> Path:
        self.data["name"] = name
        target = Path(directory) / f"{sanitize_filename(name)}.json"

        self.save(target)
        self.path = target

        return target
