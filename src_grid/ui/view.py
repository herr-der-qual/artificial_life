import math

import arcade

from ui.camera import Camera

from src_grid.simulation.world import World
from src_grid.ui.renderer import Renderer, CELL_PIXELS
from src_grid.ui.control_panel import ControlPanel
from src_grid.ui.stats_panel import StatsPanel


class View(arcade.View):
    """View for the grid rewrite's walking skeleton: a field with food and
    randomly-wandering organisms on it (see World), with the same camera
    (drag/zoom/WASD) as the pymunk world - it's plain arcade.Camera2D
    underneath, nothing pymunk-specific, so it's directly reusable.

    Ticking happens directly here (no separate SimulationRunner thread
    like the pymunk world has - the world is cheap enough, for now, that
    a background thread isn't worth the complexity). MAX_STEPS_PER_FRAME
    caps how many ticks a single frame can run, so "MAX" speed or a huge
    Step N can't stall rendering entirely.
    """

    MAX_STEPS_PER_FRAME = 500

    def __init__(self, world: World):
        super().__init__()
        self.world = world
        self.renderer = Renderer()
        self.camera = Camera()

        self.target_tps = 5.0  # ticks/sec - see ControlPanel's speed slider
        self.paused = False
        self.pending_steps = 0
        self._step_timer = 0.0

        self.control_panel = ControlPanel(self)
        self.stats_panel = StatsPanel(world)

    def on_show_view(self):
        # arcade.gui.UIManager.enable() must be called from on_show_view(),
        # not the constructor - it registers handlers on the window via
        # push_handlers, and doing that before the View's own handlers are
        # attached put ours "on top", so drags meant for a slider fell
        # through to the camera pan instead (the "slider drags the map" bug).
        self.control_panel.enable()
        self.stats_panel.enable()

    def on_hide_view(self):
        self.control_panel.disable()
        self.stats_panel.disable()

    def on_draw(self):
        self.clear()

        self.camera.use()
        self.renderer.render(self.world.grid)

        # Stats/UI stay fixed on screen regardless of the world camera's
        # pan/zoom - reset to the window's own default screen-space camera
        # before drawing them, same split WorldView uses.
        self.window.default_camera.use()
        self.control_panel.draw()
        self.stats_panel.draw()

    def on_update(self, delta_time):
        self.camera.update()
        self.stats_panel.on_update(delta_time)

        if self.pending_steps > 0:
            # Forced steps (see step()) run even while paused, and ignore
            # the speed slider entirely - only MAX_STEPS_PER_FRAME bounds
            # them, same safety valve as everything else here.
            n = min(self.pending_steps, self.MAX_STEPS_PER_FRAME)
            for _ in range(n):
                self.world.update()
            self.pending_steps -= n
            return

        if self.paused:
            return

        if self.target_tps == math.inf:
            for _ in range(self.MAX_STEPS_PER_FRAME):
                self.world.update()
            return

        self._step_timer += delta_time
        step_interval = 1.0 / self.target_tps
        steps_this_frame = 0
        while self._step_timer >= step_interval and steps_this_frame < self.MAX_STEPS_PER_FRAME:
            self._step_timer -= step_interval
            self.world.update()
            steps_this_frame += 1

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            self.toggle_pause()
            return

        if key == arcade.key.G and modifiers & arcade.key.MOD_CTRL:
            self.renderer.show_grid = not self.renderer.show_grid
            return

        self.camera.on_key_press(key, modifiers)

    def on_key_release(self, key, modifiers):
        self.camera.on_key_release(key, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_MIDDLE:
            self.toggle_pause()

    def on_mouse_drag(self, *args):
        self.camera.on_mouse_drag(*args)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.camera.on_mouse_scroll(x, y, scroll_x, scroll_y)

    # -- control panel hooks ------------------------------------------------

    def set_target_tps(self, tps):
        self.target_tps = tps

    def toggle_pause(self):
        self.paused = not self.paused
        self.control_panel.refresh_pause_button()

    def step(self, n: int):
        """Force `n` simulation ticks even while paused (pausing first, if
        not already) - mirrors SimulationRunner.step() in the pymunk
        world."""
        self.paused = True
        self.pending_steps += max(0, n)
        self.control_panel.refresh_pause_button()
