import arcade

from src_grid.simulation.world import World
from src_grid.ui.renderer import Renderer, CELL_PIXELS

STEPS_PER_SECOND = 5  # slow enough to actually see organisms move cell-to-cell, not a blur
STEP_INTERVAL = 1.0 / STEPS_PER_SECOND


class View(arcade.View):
    """Minimal view for the grid rewrite's walking skeleton: a field with
    food and randomly-wandering organisms on it (see World)."""

    def __init__(self, world: World):
        super().__init__()
        self.world = world
        self.renderer = Renderer()
        self._step_timer = 0.0

    def on_draw(self):
        self.clear()
        self.renderer.render(self.world.grid)

    def on_update(self, delta_time):
        # Discrete ticks, not a step every single frame - movement should
        # read as the field advancing cell-to-cell, not smooth sliding
        # (that's what the continuous pymunk world already does).
        self._step_timer += delta_time
        if self._step_timer >= STEP_INTERVAL:
            self._step_timer -= STEP_INTERVAL
            self.world.update()
