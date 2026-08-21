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


def main():
    config = WorldConfig()
    world = World(config)
    world.populate_async()  # spawns off the main thread - see View for the progress readout

    # Fixed window size, independent of the grid's size - same approach
    # as the pymunk system's MainWindow (see src/ui/main_window.py): the
    # grid can be far bigger than any screen, and View's Camera (drag/
    # zoom/WASD) is what navigates it, not the window growing to fit.
    screen_width, screen_height = arcade.get_display_size()
    window = arcade.Window(int(screen_width * 0.65), int(screen_height * 0.8), "Grid Field")
    arcade.set_background_color(arcade.color.BLACK)
    window.show_view(View(world))
    arcade.run()


if __name__ == "__main__":
    main()
