import tkinter as tk
from tkinter import filedialog

import arcade
import arcade.gui

from src_grid.core.world_config import WorldConfig


class NewWorldDialog:
    """Centered popup for starting a fresh world: name + width/height/
    food/organism count fields, or "Load from file..." to pull those
    fields from an existing WorldConfig preset instead of typing them.
    Confirms via on_confirm(config: WorldConfig) - this is about *starting*
    a world, not resuming one (see core.world_save / the File menu's
    Save/Load/Save As for that)."""

    WIDTH = 380
    ROW_HEIGHT = 28
    FIELD_WIDTH = 100

    def __init__(self, on_confirm):
        self.on_confirm = on_confirm

        self.manager = arcade.gui.UIManager()
        self.is_open = False

        self._build_widgets()
        self._place_initial()

    def _build_widgets(self):
        defaults = WorldConfig()  # only for sensible starting field values

        self.name_input = arcade.gui.UIInputText(text=str(defaults.get("name")), width=220, height=26)
        self.width_input = arcade.gui.UIInputText(text=str(defaults.get("width")), width=self.FIELD_WIDTH, height=26)
        self.height_input = arcade.gui.UIInputText(text=str(defaults.get("height")), width=self.FIELD_WIDTH, height=26)
        self.food_input = arcade.gui.UIInputText(text=str(defaults.get("food_count")), width=self.FIELD_WIDTH, height=26)
        self.organism_input = arcade.gui.UIInputText(
            text=str(defaults.get("organism_count")), width=self.FIELD_WIDTH, height=26,
        )

        load_button = arcade.gui.UIFlatButton(text="Load from file...", width=150, height=self.ROW_HEIGHT)
        load_button.on_click = self._on_load_click

        create_button = arcade.gui.UIFlatButton(text="Create", width=90, height=self.ROW_HEIGHT)
        create_button.on_click = self._on_create_click

        cancel_button = arcade.gui.UIFlatButton(text="Cancel", width=90, height=self.ROW_HEIGHT)
        cancel_button.on_click = self._on_cancel_click

        button_row = arcade.gui.UIBoxLayout(vertical=False, space_between=10)
        button_row.add(create_button)
        button_row.add(cancel_button)
        button_row.add(load_button)

        stack = arcade.gui.UIBoxLayout(vertical=True, align="left", space_between=10)
        stack.add(arcade.gui.UILabel(text="Create New World", width=300, font_size=14, bold=True))
        stack.add(self._row("Name:", self.name_input))
        stack.add(self._row("Width:", self.width_input))
        stack.add(self._row("Height:", self.height_input))
        stack.add(self._row("Food:", self.food_input))
        stack.add(self._row("Organisms:", self.organism_input))
        stack.add(button_row)

        self.panel = arcade.gui.UIBoxLayout(vertical=False, space_between=0)
        self.panel.with_padding(all=14)
        self.panel.with_background(color=arcade.types.Color(25, 25, 25, 245))
        self.panel.add(stack)
        self.panel.fit_content()
        self.panel.rect = self.panel.rect.resize(width=self.WIDTH)
        self.panel.visible = False

        self.manager.add(self.panel)

    @staticmethod
    def _row(label_text, widget):
        row = arcade.gui.UIBoxLayout(vertical=False, space_between=8)
        row.add(arcade.gui.UILabel(text=label_text, width=75))
        row.add(widget)
        return row

    def _place_initial(self):
        window = self.manager.window
        self.panel.rect = self.panel.rect.align_center((window.width / 2, window.height / 2))

    def open(self):
        self.is_open = True
        self.panel.visible = True

    def _close(self):
        self.is_open = False
        self.panel.visible = False

    def _on_load_click(self, event):
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            path = filedialog.askopenfilename(
                title="Load World Config",
                filetypes=[("Grid config", "*.json"), ("All files", "*.*")],
            )
        finally:
            root.destroy()

        if not path:
            return

        config = WorldConfig()
        config.load_from_file(path)
        self._fill_fields_from(config)

    def _fill_fields_from(self, config: WorldConfig):
        self.name_input.text = str(config.get("name"))
        self.width_input.text = str(config.get("width"))
        self.height_input.text = str(config.get("height"))
        self.food_input.text = str(config.get("food_count"))
        self.organism_input.text = str(config.get("organism_count"))

    def _on_create_click(self, event):
        config = self._build_config()
        if config is None:
            return

        self._close()
        self.on_confirm(config)

    def _on_cancel_click(self, event):
        self._close()

    def _build_config(self):
        try:
            width = int(self.width_input.text)
            height = int(self.height_input.text)
            food_count = int(self.food_input.text)
            organism_count = int(self.organism_input.text)
        except ValueError:
            return None

        if width <= 0 or height <= 0 or food_count < 0 or organism_count < 0:
            return None

        config = WorldConfig()
        config.data["name"] = self.name_input.text.strip() or "Untitled Grid World"
        config.data["width"] = width
        config.data["height"] = height
        config.data["food_count"] = food_count
        config.data["organism_count"] = organism_count
        config.save()  # persist as the new canonical grid_world_config.json
        return config

    # -- lifecycle ----------------------------------------------------------

    def enable(self):
        self.manager.enable()

    def disable(self):
        self.manager.disable()

    def draw(self):
        self.manager.draw()
