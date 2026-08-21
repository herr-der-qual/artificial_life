import arcade
import arcade.gui

from src_grid.simulation.organism import Organism


def _composition_text(matter) -> str:
    """A Hill-ish chemical formula (element symbols + counts, alphabetical
    - not the real Hill system's C-then-H-then-alphabetical convention,
    just consistent ordering) summed across every molecule in `matter`,
    e.g. two water molecules plus a lone carbon reads "CH4O2"."""
    counts = {}
    for molecule in matter.molecules:
        for element, count in molecule.formula().items():
            counts[element] = counts.get(element, 0) + count

    if not counts:
        return "-"

    return "".join(
        f"{element.name}{count if count > 1 else ''}"
        for element, count in sorted(counts.items(), key=lambda pair: pair[0].name)
    )


class InspectorPanel:
    """Left-side panel showing the currently selected grid entity's live
    stats (see View's right-click-to-select - left click stays free for
    camera drag, see ui.camera.Camera). Hidden until something is
    selected; right-clicking empty space clears the selection again.
    Shows different rows for an Organism vs. a plain Food/corpse -
    whichever doesn't apply just reads "-"."""

    WIDTH = 220
    TOP_MARGIN = 15
    LEFT_MARGIN = 15
    REFRESH_INTERVAL = 0.2  # faster than StatsPanel - one entity's numbers move quickly

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
        self.title_label = arcade.gui.UILabel(text="Entity", width=content_width, font_size=14, bold=True)
        stack.add(self.title_label)

        self.position_label = arcade.gui.UILabel(text="Position: (0, 0)", width=content_width)
        self.mass_label = arcade.gui.UILabel(text="Mass: 0.0", width=content_width)
        self.composition_label = arcade.gui.UILabel(text="Composition: -", width=content_width)
        self.status_label = arcade.gui.UILabel(text="Status: -", width=content_width)
        self.kind_label = arcade.gui.UILabel(text="Kind: -", width=content_width)
        self.generation_label = arcade.gui.UILabel(text="Generation: -", width=content_width)
        self.energy_label = arcade.gui.UILabel(text="Energy: -", width=content_width)
        self.drain_label = arcade.gui.UILabel(text="Drain rate: -", width=content_width)
        self.reserve_label = arcade.gui.UILabel(text="Reserve mass: -", width=content_width)
        self.cooldown_label = arcade.gui.UILabel(text="Repro cooldown: -", width=content_width)

        for label in (
            self.position_label, self.mass_label, self.composition_label, self.status_label,
            self.kind_label, self.generation_label, self.energy_label, self.drain_label,
            self.reserve_label, self.cooldown_label,
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

    def select(self, entity):
        """`entity` may be None to clear the selection (e.g. right-
        clicking empty space, or the world it belonged to got replaced)."""
        self.selected = entity
        self.panel.visible = entity is not None
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
        entity = self.selected
        if entity is None:
            return

        col, row = entity.position
        self.position_label.text = f"Position: ({col}, {row})"
        self.mass_label.text = f"Mass: {entity.matter.mass:.1f}"
        self.composition_label.text = f"Composition: {_composition_text(entity.matter)}"

        if isinstance(entity, Organism):
            self._refresh_organism(entity)
        else:
            self._refresh_food(entity)

    def _refresh_organism(self, organism: Organism):
        self.title_label.text = "Organism"
        self.status_label.text = f"Status: {'Alive' if organism.is_alive else 'Dead'}"
        self.kind_label.text = "Kind: -"
        self.generation_label.text = f"Generation: {organism.generation}"

        energy_pct = (organism.energy / organism.max_energy * 100) if organism.max_energy else 0.0
        self.energy_label.text = f"Energy: {organism.energy:.0f} / {organism.max_energy:.0f} ({energy_pct:.0f}%)"
        self.drain_label.text = f"Drain rate: {organism.energy_drain_rate:.2f}"
        self.reserve_label.text = f"Reserve mass: {organism.reserve.mass:.1f}"
        self.cooldown_label.text = f"Repro cooldown: {organism.reproduction_cooldown}"

    def _refresh_food(self, food):
        self.title_label.text = "Food"
        self.status_label.text = "Status: -"
        self.kind_label.text = f"Kind: {food.kind or '-'}"
        self.generation_label.text = "Generation: -"
        self.energy_label.text = "Energy: -"
        self.drain_label.text = "Drain rate: -"
        self.reserve_label.text = "Reserve mass: -"
        self.cooldown_label.text = "Repro cooldown: -"
