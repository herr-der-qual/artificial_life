import arcade
import arcade.gui


class StatsPanel:
    """Right-side drawer with live population statistics. Hidden by default,
    a small fixed button toggles it; it slides in/out rather than
    appearing/disappearing instantly."""

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
        self.total_label = arcade.gui.UILabel(text="Total organisms: 0", width=content_width)
        self.alive_label = arcade.gui.UILabel(text="Alive: 0", width=content_width)
        self.deaths_label = arcade.gui.UILabel(text="Deaths: 0", width=content_width)
        self.births_label = arcade.gui.UILabel(text="Born: 0", width=content_width)
        self.immigrants_label = arcade.gui.UILabel(text="Immigrants: 0", width=content_width)
        self.food_label = arcade.gui.UILabel(text="Food eaten: 0", width=content_width)
        self.predation_label = arcade.gui.UILabel(text="Predation: 0", width=content_width)
        self.energy_label = arcade.gui.UILabel(text="Avg energy: 0%", width=content_width)
        self.speed_label = arcade.gui.UILabel(text="Avg speed: 0.0", width=content_width)
        self.radius_label = arcade.gui.UILabel(text="Avg search radius: 0", width=content_width)
        self.generation_label = arcade.gui.UILabel(text="Max generation: 0", width=content_width)
        self.cell_count_label = arcade.gui.UILabel(text="Avg/Max cells: 0.0 / 0", width=content_width)
        self.predator_pct_label = arcade.gui.UILabel(text="Predators: 0%", width=content_width)
        self.herbivore_pct_label = arcade.gui.UILabel(text="Herbivores: 0%", width=content_width)
        self.mineral_pct_label = arcade.gui.UILabel(text="Mineral eaters: 0%", width=content_width)

        for label in (
            self.total_label, self.alive_label, self.deaths_label, self.births_label, self.immigrants_label,
            self.food_label, self.predation_label, self.energy_label, self.speed_label, self.radius_label,
            self.generation_label, self.cell_count_label,
            self.predator_pct_label, self.herbivore_pct_label, self.mineral_pct_label,
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
        organisms = list(self.world.organisms)
        alive = len(organisms)

        self.total_label.text = f"Total organisms: {self.world.total_organisms_count}"
        self.alive_label.text = f"Alive: {alive}"
        self.deaths_label.text = f"Deaths: {self.world.deaths_count}"
        self.births_label.text = f"Born: {self.world.births_count}"
        self.immigrants_label.text = f"Immigrants: {self.world.immigrants_count}"
        self.food_label.text = f"Food eaten: {self.world.food_eaten_count} (left: {len(self.world.substances)})"
        self.predation_label.text = f"Predation: {self.world.predation_count}"

        if organisms:
            avg_energy_ratio = sum(o.energy / o.max_energy for o in organisms) / alive * 100
            avg_speed = sum(o.genome.speed for o in organisms) / alive
            avg_radius = sum(o.genome.search_radius for o in organisms) / alive
            avg_cell_count = sum(o.cell_count for o in organisms) / alive
            max_cell_count = max(o.cell_count for o in organisms)
            # Independent percentages, not mutually exclusive buckets - diet
            # is a set of flags (an organism can be a generalist eating all
            # three), so these can add up to more than 100%.
            predator_pct = sum(1 for o in organisms if "flesh" in o.diet) / alive * 100
            herbivore_pct = sum(1 for o in organisms if o.diet & {"basic", "rich", "simple"}) / alive * 100
            mineral_pct = sum(1 for o in organisms if "mineral" in o.diet) / alive * 100
        else:
            avg_energy_ratio = 0.0
            avg_speed = 0.0
            avg_radius = 0.0
            avg_cell_count = 0.0
            max_cell_count = 0
            predator_pct = 0.0
            herbivore_pct = 0.0
            mineral_pct = 0.0

        self.energy_label.text = f"Avg energy: {avg_energy_ratio:.0f}%"
        self.speed_label.text = f"Avg speed: {avg_speed:.1f}"
        self.radius_label.text = f"Avg search radius: {avg_radius:.0f}"
        self.generation_label.text = f"Max generation: {self.world.max_generation_reached}"
        self.cell_count_label.text = f"Avg/Max cells: {avg_cell_count:.1f} / {max_cell_count}"
        self.predator_pct_label.text = f"Predators: {predator_pct:.0f}%"
        self.herbivore_pct_label.text = f"Herbivores: {herbivore_pct:.0f}%"
        self.mineral_pct_label.text = f"Mineral eaters: {mineral_pct:.0f}%"
