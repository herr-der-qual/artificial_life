import math
from pathlib import Path

import arcade

from ui.camera import Camera
from ui.save_as_dialog import SaveAsDialog

from src_grid.simulation.world import World
from src_grid.core.world_config import sanitize_filename
from src_grid.core.world_save import save_world, load_world, GRID_SAVES_DIR
from src_grid.ui.renderer import Renderer, CELL_PIXELS
from src_grid.ui.control_panel import ControlPanel
from src_grid.ui.stats_panel import StatsPanel
from src_grid.ui.file_menu import FileMenu
from src_grid.ui.new_world_dialog import NewWorldDialog


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

        self.file_menu = FileMenu(
            on_new_world=self._open_new_world_dialog,
            on_save=self._save_world,
            on_load=self._load_world_from_path,
            on_save_as=self._open_save_as_dialog,
        )
        self.new_world_dialog = NewWorldDialog(on_confirm=self._create_new_world)

        default_dir = GRID_SAVES_DIR if GRID_SAVES_DIR.exists() else None
        self.save_as_dialog = SaveAsDialog(on_confirm=self._save_world_as, default_directory=default_dir)

    def on_show_view(self):
        # arcade.gui.UIManager.enable() must be called from on_show_view(),
        # not the constructor - it registers handlers on the window via
        # push_handlers, and doing that before the View's own handlers are
        # attached put ours "on top", so drags meant for a slider fell
        # through to the camera pan instead (the "slider drags the map" bug).
        self.control_panel.enable()
        self.stats_panel.enable()
        self.file_menu.enable()
        self.new_world_dialog.enable()
        self.save_as_dialog.enable()

    def on_hide_view(self):
        self.control_panel.disable()
        self.stats_panel.disable()
        self.file_menu.disable()
        self.new_world_dialog.disable()
        self.save_as_dialog.disable()

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
        self.file_menu.draw()
        self.new_world_dialog.draw()
        self.save_as_dialog.draw()

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

        if key == arcade.key.S and modifiers & arcade.key.MOD_CTRL:
            save_world(self.world)
            return

        if key == arcade.key.L and modifiers & arcade.key.MOD_CTRL:
            self._load_saved_world()
            return

        if key == arcade.key.R and modifiers & arcade.key.MOD_CTRL:
            self._restart_world()
            return

        self.camera.on_key_press(key, modifiers)

    def _load_saved_world(self):
        try:
            self.world = load_world()
        except FileNotFoundError:
            return

        self.stats_panel.world = self.world

    def _restart_world(self):
        """Re-read the active config off disk (in case it was hand-edited
        or swapped via NewWorldDialog's "Load from file...") and spin up a
        fresh world from it - a reset, not a resume, unlike Ctrl+L."""
        self.world.config.load()
        self.world = World(self.world.config)
        self.stats_panel.world = self.world

    # -- file menu / dialogs hooks -------------------------------------------

    def _open_new_world_dialog(self):
        self.new_world_dialog.open()

    def _create_new_world(self, config):
        self.world = World(config)
        self.stats_panel.world = self.world

    def _save_world(self):
        save_world(self.world)

    def _load_world_from_path(self, path):
        self.world = load_world(Path(path))
        self.stats_panel.world = self.world

    def _open_save_as_dialog(self):
        self.save_as_dialog.open(default_name=self.world.config.get("name"))

    def _save_world_as(self, directory, name):
        target = Path(directory) / f"{sanitize_filename(name)}.json"
        save_world(self.world, target)

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
