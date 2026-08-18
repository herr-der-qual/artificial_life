import math

import arcade

from core.settings import Settings
from core.sumulation_runner import SimulationRunner
from simulation.world import World
from .camera import Camera
from .renderer import Renderer
from .control_panel import ControlPanel


class WorldView(arcade.View):
    def __init__(self):
        super().__init__()

        self.camera = Camera()
        self.world = World()
        self.renderer = Renderer()
        self.renderer.initialize(self.world.organisms + self.world.substances)

        self.settings = Settings()

        saved_fps = self.settings.get("target_fps")
        target_fps = math.inf if saved_fps == "infinite" else saved_fps

        self.runner = SimulationRunner(
            self.world,
            target_fps=target_fps,
            paused=self.settings.get("paused"),
        )
        self.runner.start()

        self.control_panel = ControlPanel(self.runner, self.settings)

    def on_show_view(self):
        self.control_panel.enable()

    def on_hide_view(self):
        self.control_panel.disable()

    def on_draw(self):
        self.clear()
        self.camera.use()

        center = arcade.XYWH(-2.5, -2.5, 5, 5)
        arcade.draw_rect_filled(center, (255, 255, 255))

        self.renderer.render(self.world.organisms + self.world.substances)

        self.control_panel.draw()

    def on_update(self, delta_time):
        self.camera.update()
        self.control_panel.on_update(delta_time)

    def on_key_press(self, key, modifiers):
        self.camera.on_key_press(key, modifiers)

    def on_key_release(self, key, modifiers):
        self.camera.on_key_release(key, modifiers)

    def on_mouse_drag(self, *args):
        self.camera.on_mouse_drag(*args)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.camera.on_mouse_scroll(x, y, scroll_x, scroll_y)
