import sys
from pathlib import Path

# Bootstrap both roots onto sys.path so this runs the same way whether
# invoked directly (`python src_grid/main.py`, which only puts src_grid/
# itself on sys.path) or as a module (`python -m src_grid.main`, which
# puts the repo root on sys.path but not src/) - grid-system code reuses
# chemistry/rendering helpers straight from the pymunk system's src/ tree.
_REPO_ROOT = Path(__file__).resolve().parent.parent
for _path in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import arcade

from src_grid.core.world_config import WorldConfig
from src_grid.simulation.world import World
from src_grid.ui.view import View
from src_grid.ui.renderer import CELL_PIXELS


def main():
    config = WorldConfig()
    world = World(config)

    window = arcade.Window(config.get("width") * CELL_PIXELS, config.get("height") * CELL_PIXELS, "Grid Field")
    arcade.set_background_color(arcade.color.BLACK)
    window.show_view(View(world))
    arcade.run()


if __name__ == "__main__":
    main()
