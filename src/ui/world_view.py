import arcade

from core.sumulation_runner import SimulationRunner
from simulation.world import World
from .camera import Camera
from .renderer import Renderer


class WorldView(arcade.View):
    def __init__(self):
        super().__init__()

        self.camera = Camera()
        self.world = World()
        self.renderer = Renderer()
        self.renderer.initialize(self.world.organisms + self.world.substances)

        self.runner = SimulationRunner(self.world)
        self.runner.start()

    def on_draw(self):
        self.clear()
        self.camera.use()

        center = arcade.XYWH(-2.5, -2.5, 5, 5)
        arcade.draw_rect_filled(center, (255, 255, 255))

        self.renderer.render(self.world.organisms + self.world.substances)

    def on_update(self, delta_time):
        self.camera.update()

    def on_key_press(self, key, modifiers):
        self.camera.on_key_press(key, modifiers)

    def on_key_release(self, key, modifiers):
        self.camera.on_key_release(key, modifiers)

    def on_mouse_drag(self, *args):
        self.camera.on_mouse_drag(*args)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.camera.on_mouse_scroll(x, y, scroll_x, scroll_y)
