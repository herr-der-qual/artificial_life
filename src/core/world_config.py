import json
import re
from pathlib import Path

WORLD_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "world_config.json"
WORLD_CONFIGS_DIR = Path(__file__).resolve().parent.parent.parent / "world_configs"

DEFAULTS = {
    "name": "Untitled World",
    "initial_organism_count": 10,
    "initial_substance_count": 50,
    "organism_spawn_bound": 300.0,
    "substance_spawn_bound": 400.0,
    "food_spawn_interval": 5.0,   # seconds between food trickle spawns, 0 disables
    "food_spawn_count": 3,        # substances spawned per trickle
    "max_substance_count": 150,   # soft cap so the trickle can't grow unbounded
}

_UNSAFE_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def sanitize_filename(name: str) -> str:
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", name).strip()
    return cleaned or "world"


class WorldConfig:
    """JSON-backed world generation settings. The 'initial/default' values
    live purely as DEFAULTS in code - the only file on disk is always the
    single *current* active config (mirrors core/settings.py)."""

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
        """Adopt another world config file as the active one: read it, then
        persist it into the canonical world_config.json - there is never a
        second file, the current one just gets overwritten."""
        self.load(Path(source_path))
        self.save()

    def save_as(self, directory, name: str) -> Path:
        """Save the current settings under `name` inside `directory`, and
        make that file the active one for the rest of this session (further
        plain saves go there, mirroring a normal app's "Save As")."""
        self.data["name"] = name
        target = Path(directory) / f"{sanitize_filename(name)}.json"

        self.save(target)
        self.path = target

        return target
