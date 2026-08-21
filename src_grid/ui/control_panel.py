import arcade
import arcade.gui

from core.speed_scale import slider_to_fps, fps_to_slider, format_fps


class ControlPanel:
    """Bottom-bar controls: speed slider, pause, step. Mirrors the pymunk
    world's ControlPanel, minus Settings persistence and the threaded
    SimulationRunner - the grid world's tick loop lives directly on the
    View's on_update, no background thread to decouple render/step rate
    from (see View.MAX_STEPS_PER_FRAME for how "fast" stays bounded)."""

    def __init__(self, view):
        self.view = view
        self.manager = arcade.gui.UIManager()

        self._build_widgets()
        self._layout()

    def _build_widgets(self):
        self.speed_slider = arcade.gui.UISlider(
            value=fps_to_slider(self.view.target_tps), min_value=0.0, max_value=1.0, width=150,
        )
        self.speed_label = arcade.gui.UILabel(text=format_fps(self.view.target_tps), width=36)

        self.pause_button = arcade.gui.UIFlatButton(text=self._pause_text(), width=80)

        self.n_input = arcade.gui.UIInputText(text="10", width=45, height=26)
        self.step_button = arcade.gui.UIFlatButton(text="Step N", width=70)
        self.step2_button = arcade.gui.UIFlatButton(text="Step 2N", width=75)

        self.speed_slider.on_change = self._on_speed_change
        self.pause_button.on_click = self._on_pause_click
        self.step_button.on_click = self._on_step_click
        self.step2_button.on_click = self._on_step2_click

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
        return "Resume" if self.view.paused else "Pause"

    def refresh_pause_button(self):
        """Called by View whenever pause is toggled from anywhere (button,
        Space, middle-click, Step) so the label always matches reality."""
        self.pause_button.text = self._pause_text()

    # -- widget callbacks ---------------------------------------------------

    def _on_speed_change(self, event):
        tps = slider_to_fps(event.new_value)
        self.view.set_target_tps(tps)
        self.speed_label.text = format_fps(tps)

    def _on_pause_click(self, event):
        self.view.toggle_pause()

    def _on_step_click(self, event):
        self._request_steps(1)

    def _on_step2_click(self, event):
        self._request_steps(2)

    def _request_steps(self, multiplier: int):
        n = self._parse_n()
        if n is None:
            return
        self.view.step(n * multiplier)

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
