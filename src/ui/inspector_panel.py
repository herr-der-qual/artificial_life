import arcade
import arcade.gui


class InspectorPanel:
    """Left-side panel showing the currently selected organism's live
    stats (see WorldView's click-to-select). Hidden until something is
    selected; clicking empty space clears the selection again."""

    WIDTH = 220
    TOP_MARGIN = 15
    LEFT_MARGIN = 15
    REFRESH_INTERVAL = 0.2  # faster than StatsPanel - one organism's numbers move quickly

    def __init__(self):
        self.manager = arcade.gui.UIManager()
        self.selected = None
        self._refresh_timer = 0.0

        self._build_widgets()
        self._place_initial()
        self._refresh()

    def _build_widgets(self):
        content_width = self.WIDTH - 24

        stack = arcade.gui.UIBoxLayout(vertical=True, align="left", space_between=4)
        stack.add(arcade.gui.UILabel(text="Organism", width=content_width, font_size=14, bold=True))

        self.status_label = arcade.gui.UILabel(text="Status: Alive", width=content_width)
        self.generation_label = arcade.gui.UILabel(text="Generation: 0", width=content_width)
        self.energy_label = arcade.gui.UILabel(text="Energy: 0 / 0 (0%)", width=content_width)
        self.speed_label = arcade.gui.UILabel(text="Speed: 0.0", width=content_width)
        self.cell_count_label = arcade.gui.UILabel(text="Cells: 0", width=content_width)
        self.search_radius_label = arcade.gui.UILabel(text="Search radius: 0", width=content_width)
        self.wander_radius_label = arcade.gui.UILabel(text="Wander radius: 0", width=content_width)
        self.reserve_label = arcade.gui.UILabel(text="Reserve mass: 0.0", width=content_width)
        self.cooldown_label = arcade.gui.UILabel(text="Repro cooldown: 0.0", width=content_width)
        self.diet_label = arcade.gui.UILabel(text="Diet: -", width=content_width)
        self.position_label = arcade.gui.UILabel(text="Position: (0, 0)", width=content_width)

        for label in (
            self.status_label, self.generation_label, self.energy_label, self.speed_label,
            self.cell_count_label, self.search_radius_label, self.wander_radius_label,
            self.reserve_label, self.cooldown_label, self.diet_label, self.position_label,
        ):
            stack.add(label)

        self.panel = arcade.gui.UIBoxLayout(vertical=False, space_between=0)
        self.panel.with_padding(all=12)
        self.panel.with_background(color=arcade.types.Color(20, 20, 20, 220))
        self.panel.add(stack)
        self.panel.fit_content()
        # fit_content() sizes width from labels' natural text content, not
        # the explicit width= we gave them - pin it to a fixed panel width.
        self.panel.rect = self.panel.rect.resize(width=self.WIDTH)
        self.panel.visible = False

        self.manager.add(self.panel)

    def _place_initial(self):
        window = self.manager.window
        top = window.height - self.TOP_MARGIN
        self.panel.rect = self.panel.rect.align_top(top).align_left(self.LEFT_MARGIN)

    # -- selection ------------------------------------------------------

    def select(self, organism):
        """`organism` may be None to clear the selection (e.g. clicking
        empty space)."""
        self.selected = organism
        self.panel.visible = organism is not None
        self._refresh()

    # -- lifecycle ----------------------------------------------------------

    def enable(self):
        self.manager.enable()

    def disable(self):
        self.manager.disable()

    def draw(self):
        self.manager.draw()

    def on_update(self, delta_time):
        self._refresh_timer += delta_time
        if self._refresh_timer >= self.REFRESH_INTERVAL:
            self._refresh_timer = 0.0
            self._refresh()

    # -- internals ------------------------------------------------------

    def _refresh(self):
        organism = self.selected
        if organism is None:
            return

        self.status_label.text = f"Status: {'Alive' if organism.is_alive else 'Dead'}"
        self.generation_label.text = f"Generation: {organism.generation}"

        energy_pct = (organism.energy / organism.max_energy * 100) if organism.max_energy else 0.0
        self.energy_label.text = f"Energy: {organism.energy:.0f} / {organism.max_energy:.0f} ({energy_pct:.0f}%)"

        self.speed_label.text = f"Speed: {organism.speed:.1f}"
        self.cell_count_label.text = f"Cells: {organism.cell_count}"
        self.search_radius_label.text = f"Search radius: {organism.search_radius:.0f}"
        self.wander_radius_label.text = f"Wander radius: {organism.wander_radius:.0f}"
        self.reserve_label.text = f"Reserve mass: {organism.reserve.mass:.1f}"
        self.cooldown_label.text = f"Repro cooldown: {organism.reproduction_cooldown:.1f}"
        self.diet_label.text = f"Diet: {', '.join(sorted(organism.diet)) or '-'}"
        self.position_label.text = f"Position: ({organism.position.x:.0f}, {organism.position.y:.0f})"
