import json
import time
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent / "settings.json"

DEFAULTS = {
    "target_fps": 60,       # number, or "infinite" for uncapped speed
    "paused": False,
    "step_n": 10,
    "stats_panel_open": False,
    "ui_hidden": False,
}

FLUSH_INTERVAL = 0.5  # seconds - avoids hammering disk while a slider is being dragged


class Settings:
    """Simple JSON-backed key/value store for UI-configurable simulation
    settings. Writes are debounced: set() only marks the store dirty,
    maybe_flush() (called once per frame) performs the actual disk write at
    most every FLUSH_INTERVAL seconds."""

    def __init__(self, path: Path = SETTINGS_PATH):
        self.path = path
        self.data = dict(DEFAULTS)
        self._dirty = False
        self._last_flush = 0.0
        self.load()

    def load(self):
        if not self.path.exists():
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except (OSError, json.JSONDecodeError):
            return

        for key in DEFAULTS:
            if key in loaded:
                self.data[key] = loaded[key]

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        self._dirty = False
        self._last_flush = time.time()

    def get(self, key):
        return self.data.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        if self.data.get(key) == value:
            return
        self.data[key] = value
        self._dirty = True

    def maybe_flush(self):
        if self._dirty and (time.time() - self._last_flush) >= FLUSH_INTERVAL:
            self.save()
