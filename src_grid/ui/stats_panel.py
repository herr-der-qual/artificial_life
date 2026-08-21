import arcade
import arcade.gui


class StatsPanel:
    """Right-side drawer with live population statistics - mirrors the
    pymunk world's StatsPanel (same slide-out mechanic, toggle button)."""

    WIDTH = 240
    TOP_MARGIN = 15
    SLIDE_SPEED = 1400  # px/sec
    REFRESH_INTERVAL = 0.5
    BUTTON_SIZE = 32

    def __init__(self, world):
        self.world = world
        self.manager = arcade.gui.UIManager()
        self.is_open = False
        self._refresh_timer = 0.0

        self._build_widgets()
        self._place_initial()
        self._refresh_stats()

    def _build_widgets(self):
        content_width = self.WIDTH - 24

        stack = arcade.gui.UIBoxLayout(vertical=True, align="left", space_between=4)
        stack.add(arcade.gui.UILabel(text="Statistics", width=content_width, font_size=14, bold=True))

        # Seeded with placeholder text (not "") so their rect has a real
        # height from the start - UIBoxLayout sizes itself from children's
        # current rect, which an empty UILabel reports as zero-height until
        # its own fit_content() runs.
        self.tick_label = arcade.gui.UILabel(text="Tick: 0", width=content_width)
        self.alive_label = arcade.gui.UILabel(text="Alive: 0", width=content_width)
        self.food_label = arcade.gui.UILabel(text="Food: 0", width=content_width)

        self.deaths_label = arcade.gui.UILabel(text="Deaths: 0", width=content_width)
        self.food_eaten_label = arcade.gui.UILabel(text="Food eaten: 0", width=content_width)
        self.energy_label = arcade.gui.UILabel(text="Avg energy: -", width=content_width)
        self.births_label = arcade.gui.UILabel(text="Born: 0", width=content_width)
        self.generation_label = arcade.gui.UILabel(text="Max generation: 0", width=content_width)

        for label in (
            self.tick_label, self.alive_label, self.food_label,
            self.deaths_label, self.births_label, self.food_eaten_label,
            self.energy_label, self.generation_label,
        ):
            stack.add(label)

        self.panel = arcade.gui.UIBoxLayout(vertical=False, space_between=0)
        self.panel.with_padding(all=12)
        self.panel.with_background(color=arcade.types.Color(20, 20, 20, 220))
        self.panel.add(stack)
        self.panel.fit_content()
        # fit_content() sizes width from labels' natural text content, not
        # the explicit width= we gave them - pin it to a fixed drawer width.
        self.panel.rect = self.panel.rect.resize(width=self.WIDTH)

        self.toggle_button = arcade.gui.UIFlatButton(text="☰", width=self.BUTTON_SIZE, height=self.BUTTON_SIZE)
        self.toggle_button.on_click = self._on_toggle

        self.manager.add(self.panel)
        self.manager.add(self.toggle_button)

    def _place_initial(self):
        window = self.manager.window

        top = window.height - self.TOP_MARGIN
        self.panel.rect = self.panel.rect.align_top(top).align_left(window.width)

        button_top = window.height / 2 + self.BUTTON_SIZE / 2
        button_left = window.width - self.BUTTON_SIZE - 6
        self.toggle_button.rect = self.toggle_button.rect.align_top(button_top).align_left(button_left)

    def _on_toggle(self, event):
        self.is_open = not self.is_open

    # -- lifecycle ----------------------------------------------------------

    def enable(self):
        self.manager.enable()

    def disable(self):
        self.manager.disable()

    def draw(self):
        self.manager.draw()

    def on_update(self, delta_time):
        self._animate(delta_time)

        self._refresh_timer += delta_time
        if self._refresh_timer >= self.REFRESH_INTERVAL:
            self._refresh_timer = 0.0
            self._refresh_stats()

    # -- internals ------------------------------------------------------

    def _animate(self, delta_time):
        window = self.manager.window
        target_left = (window.width - self.WIDTH) if self.is_open else window.width

        current_left = self.panel.rect.left
        if current_left == target_left:
            return

        step = self.SLIDE_SPEED * delta_time
        if current_left < target_left:
            new_left = min(current_left + step, target_left)
        else:
            new_left = max(current_left - step, target_left)

        self.panel.rect = self.panel.rect.align_left(new_left)

    def _refresh_stats(self):
        alive = len(self.world.organisms)
        food = len(self.world.grid) - alive
        avg_energy = sum(o.energy for o in self.world.organisms) / alive if alive else 0.0

        self.tick_label.text = f"Tick: {self.world.tick_count}"
        self.alive_label.text = f"Alive: {alive}"
        self.food_label.text = f"Food: {food}"
        self.deaths_label.text = f"Deaths: {self.world.deaths_count}"
        self.food_eaten_label.text = f"Food eaten: {self.world.food_eaten_count}"
        self.energy_label.text = f"Avg energy: {avg_energy:.1f}"
        self.births_label.text = f"Born: {self.world.births_count}"
        self.generation_label.text = f"Max generation: {self.world.max_generation_reached}"
