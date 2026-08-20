import math

import arcade
import arcade.gui

from core.settings import Settings
from core.speed_scale import slider_to_fps, fps_to_slider, format_fps
from core.sumulation_runner import SimulationRunner


class ControlPanel:
    """Bottom-bar simulation controls: speed slider, pause, and frame
    stepping. All changes are mirrored into Settings (debounced JSON writes,
    flushed from on_update)."""

    def __init__(self, runner: SimulationRunner, settings: Settings):
        self.runner = runner
        self.settings = settings
        self.manager = arcade.gui.UIManager()

        self._build_widgets()
        self._layout()

    def _build_widgets(self):
        self.speed_slider = arcade.gui.UISlider(
            value=fps_to_slider(self.runner.target_fps),
            min_value=0.0,
            max_value=1.0,
            width=150,
        )
        self.speed_label = arcade.gui.UILabel(
            text=format_fps(self.runner.target_fps), width=36,
        )

        self.pause_button = arcade.gui.UIFlatButton(
            text=self._pause_text(), width=80,
        )

        self.n_input = arcade.gui.UIInputText(
            text=str(self.settings.get("step_n")), width=45, height=26,
        )

        self.step_button = arcade.gui.UIFlatButton(text="Step N", width=70)
        self.step2_button = arcade.gui.UIFlatButton(text="Step 2N", width=75)

        self.show_hitboxes = self.settings.get("show_hitboxes")
        self.hitboxes_button = arcade.gui.UIFlatButton(
            text=self._hitboxes_text(), width=110,
        )

        self.speed_slider.on_change = self._on_speed_change
        self.pause_button.on_click = self._on_pause_click
        self.n_input.on_change = self._on_n_change
        self.step_button.on_click = self._on_step_click
        self.step2_button.on_click = self._on_step2_click
        self.hitboxes_button.on_click = self._on_hitboxes_click

    def _layout(self):
        speed_row = arcade.gui.UIBoxLayout(vertical=False, space_between=8)
        speed_row.add(arcade.gui.UILabel(text="Speed:", width=48))
        speed_row.add(self.speed_slider)
        speed_row.add(self.speed_label)
        speed_row.add(self.pause_button)

        step_row = arcade.gui.UIBoxLayout(vertical=False, space_between=8)
        step_row.add(arcade.gui.UILabel(text="N:", width=15))
        step_row.add(self.n_input)
        step_row.add(self.step_button)
        step_row.add(self.step2_button)
        step_row.add(self.hitboxes_button)

        stack = arcade.gui.UIBoxLayout(vertical=True, align="left", space_between=6)
        stack.add(speed_row)
        stack.add(step_row)

        panel = arcade.gui.UIBoxLayout(vertical=False, space_between=10)
        panel.with_padding(all=10)
        panel.with_background(color=arcade.types.Color(20, 20, 20, 200))
        panel.add(stack)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(child=panel, anchor_x="center", anchor_y="bottom", align_y=15)

        self.manager.add(anchor)

    # -- state -> widgets -------------------------------------------------

    def _pause_text(self) -> str:
        return "Resume" if self.runner.paused else "Pause"

    def _refresh_pause_button(self):
        self.pause_button.text = self._pause_text()

    def _hitboxes_text(self) -> str:
        return f"Hitboxes: {'On' if self.show_hitboxes else 'Off'}"

    # -- widget callbacks ---------------------------------------------------

    def _on_speed_change(self, event):
        fps = slider_to_fps(event.new_value)
        self.runner.set_target_fps(fps)
        self.speed_label.text = format_fps(fps)
        self.settings.set("target_fps", "infinite" if fps == math.inf else fps)

    def _on_pause_click(self, event):
        self.toggle_pause()

    def toggle_pause(self):
        """Shared by the Pause button and any other trigger (e.g. a
        middle-mouse-button shortcut) so the button label and settings
        always stay in sync with however playback got toggled."""
        self.runner.toggle_pause()
        self._refresh_pause_button()
        self.settings.set("paused", self.runner.paused)

    def _on_hitboxes_click(self, event):
        self.toggle_hitboxes()

    def toggle_hitboxes(self):
        """Shared by the button and the Ctrl+B shortcut (see WorldView)."""
        self.show_hitboxes = not self.show_hitboxes
        self.hitboxes_button.text = self._hitboxes_text()
        self.settings.set("show_hitboxes", self.show_hitboxes)

    def _on_n_change(self, event):
        n = self._parse_n()
        if n is not None:
            self.settings.set("step_n", n)

    def _on_step_click(self, event):
        self._request_steps(1)

    def _on_step2_click(self, event):
        self._request_steps(2)

    def _request_steps(self, multiplier: int):
        n = self._parse_n()
        if n is None:
            return

        self.runner.step(n * multiplier)
        self._refresh_pause_button()

    def _parse_n(self):
        try:
            n = int(self.n_input.text)
        except ValueError:
            return None
        return n if n > 0 else None

    # -- lifecycle ----------------------------------------------------------

    def enable(self):
        self.manager.enable()

    def disable(self):
        self.manager.disable()

    def draw(self):
        self.manager.draw()

    def on_update(self, delta_time):
        self.settings.maybe_flush()
