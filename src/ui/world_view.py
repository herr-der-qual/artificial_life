import math

import arcade

from core.settings import Settings
from core.sumulation_runner import SimulationRunner
from core.world_config import WorldConfig, WORLD_CONFIGS_DIR
from simulation.world import World
from .camera import Camera
from .renderer import Renderer
from .control_panel import ControlPanel
from .stats_panel import StatsPanel
from .file_menu import FileMenu
from .save_as_dialog import SaveAsDialog


class WorldView(arcade.View):
    def __init__(self):
        super().__init__()

        self.camera = Camera()

        self.settings = Settings()
        self.world_config = WorldConfig()
        self.world = World(self.world_config)

        self.renderer = Renderer()
        self.renderer.initialize(self.world.organisms + self.world.substances)

        saved_fps = self.settings.get("target_fps")
        target_fps = math.inf if saved_fps == "infinite" else saved_fps

        self.runner = SimulationRunner(
            self.world,
            target_fps=target_fps,
            paused=self.settings.get("paused"),
        )
        self.runner.start()

        self.control_panel = ControlPanel(self.runner, self.settings)
        self.stats_panel = StatsPanel(self.world)
        self.stats_panel.is_open = self.settings.get("stats_panel_open")
        self.file_menu = FileMenu(on_load=self.load_world, on_save=self.save_world, on_save_as=self.open_save_as_dialog)

        default_dir = WORLD_CONFIGS_DIR if WORLD_CONFIGS_DIR.exists() else None
        self.save_as_dialog = SaveAsDialog(on_confirm=self.save_world_as, default_directory=default_dir)

        self.ui_hidden = self.settings.get("ui_hidden")

    def load_world(self, path):
        """Adopt `path` as the active world config and rebuild the running
        world from it - also the future body of a Ctrl+R restart, which
        would just call this with self.world_config.path instead."""
        self.world_config.load_from_file(path)

        with self.runner.lock:
            self.world = World(self.world_config)
            self.runner.world = self.world

        self.renderer.initialize(self.world.organisms + self.world.substances)
        self.stats_panel.world = self.world

    def save_world(self):
        self.world_config.save()

    def open_save_as_dialog(self):
        self.save_as_dialog.open(default_name=self.world_config.get("name"))

    def save_world_as(self, directory, name):
        self.world_config.save_as(directory, name)

    def on_show_view(self):
        self._set_ui_enabled(not self.ui_hidden)

    def on_hide_view(self):
        self._set_ui_enabled(False)

    def on_draw(self):
        self.clear()
        self.camera.use()

        center = arcade.XYWH(-2.5, -2.5, 5, 5)
        arcade.draw_rect_filled(center, (255, 255, 255))

        self.renderer.render(self.world.organisms + self.world.substances)

        if not self.ui_hidden:
            self.control_panel.draw()
            self.stats_panel.draw()
            self.file_menu.draw()
            self.save_as_dialog.draw()

    def on_update(self, delta_time):
        self.camera.update()
        self.control_panel.on_update(delta_time)
        self.stats_panel.on_update(delta_time)
        self.settings.set("stats_panel_open", self.stats_panel.is_open)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.H and modifiers & arcade.key.MOD_CTRL:
            self._toggle_ui_hidden()
            return

        if key == arcade.key.S and modifiers & arcade.key.MOD_CTRL:
            self.save_world()
            return

        self.camera.on_key_press(key, modifiers)

    def on_key_release(self, key, modifiers):
        self.camera.on_key_release(key, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_MIDDLE:
            self.control_panel.toggle_pause()

    def on_mouse_drag(self, *args):
        self.camera.on_mouse_drag(*args)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.camera.on_mouse_scroll(x, y, scroll_x, scroll_y)

    def _toggle_ui_hidden(self):
        self.ui_hidden = not self.ui_hidden
        self._set_ui_enabled(not self.ui_hidden)
        self.settings.set("ui_hidden", self.ui_hidden)

    def _set_ui_enabled(self, enabled: bool):
        panels = (self.control_panel, self.stats_panel, self.file_menu, self.save_as_dialog)
        for panel in panels:
            panel.enable() if enabled else panel.disable()
