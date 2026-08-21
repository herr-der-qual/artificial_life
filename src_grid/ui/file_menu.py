import tkinter as tk
from tkinter import filedialog

import arcade
import arcade.gui


class FileMenu:
    """Top-left "File" menu: New World / Save / Load / Save As...

    Save/Load/Save As all operate on a full LIVE WORLD SAVE (see
    core.world_save) - exact positions, matter, tick count - not the
    start recipe (see NewWorldDialog / core.world_config for that).
    Load opens a native file picker and forwards the chosen path to
    on_load. Save fires on_save directly (the canonical save file).
    Save As... fires on_save_as, which the owner is expected to handle
    by opening a SaveAsDialog. New World... fires on_new_world, which
    the owner is expected to handle by opening a NewWorldDialog."""

    WIDTH = 170
    TOP_MARGIN = 10
    LEFT_MARGIN = 10
    BUTTON_HEIGHT = 28

    def __init__(self, on_new_world, on_save, on_load, on_save_as):
        self.on_new_world = on_new_world
        self.on_save = on_save
        self.on_load = on_load
        self.on_save_as = on_save_as

        self.manager = arcade.gui.UIManager()
        self.is_open = False

        self._build_widgets()
        self._place_initial()

    def _build_widgets(self):
        self.file_button = arcade.gui.UIFlatButton(text="File", width=70, height=self.BUTTON_HEIGHT)
        self.file_button.on_click = self._on_toggle

        button_width = self.WIDTH - 16
        self.new_world_button = arcade.gui.UIFlatButton(
            text="New World...", width=button_width, height=self.BUTTON_HEIGHT,
        )
        self.save_button = arcade.gui.UIFlatButton(text="Save", width=button_width, height=self.BUTTON_HEIGHT)
        self.load_button = arcade.gui.UIFlatButton(text="Load", width=button_width, height=self.BUTTON_HEIGHT)
        self.save_as_button = arcade.gui.UIFlatButton(
            text="Save As...", width=button_width, height=self.BUTTON_HEIGHT,
        )

        self.new_world_button.on_click = self._on_new_world_click
        self.save_button.on_click = self._on_save_click
        self.load_button.on_click = self._on_load_click
        self.save_as_button.on_click = self._on_save_as_click

        self.dropdown_panel = arcade.gui.UIBoxLayout(vertical=True, space_between=4)
        self.dropdown_panel.with_padding(all=8)
        self.dropdown_panel.with_background(color=arcade.types.Color(20, 20, 20, 230))
        self.dropdown_panel.add(self.new_world_button)
        self.dropdown_panel.add(self.save_button)
        self.dropdown_panel.add(self.load_button)
        self.dropdown_panel.add(self.save_as_button)
        self.dropdown_panel.fit_content()
        self.dropdown_panel.rect = self.dropdown_panel.rect.resize(width=self.WIDTH)
        self.dropdown_panel.visible = False

        self.manager.add(self.file_button)
        self.manager.add(self.dropdown_panel)

    def _place_initial(self):
        window = self.manager.window
        top = window.height - self.TOP_MARGIN

        self.file_button.rect = self.file_button.rect.align_top(top).align_left(self.LEFT_MARGIN)
        dropdown_top = self.file_button.rect.bottom - 4
        self.dropdown_panel.rect = self.dropdown_panel.rect.align_top(dropdown_top).align_left(self.LEFT_MARGIN)

    def _on_toggle(self, event):
        self.is_open = not self.is_open
        self.dropdown_panel.visible = self.is_open

    def _close(self):
        self.is_open = False
        self.dropdown_panel.visible = False

    def _on_new_world_click(self, event):
        self._close()
        self.on_new_world()

    def _on_save_click(self, event):
        self._close()
        self.on_save()

    def _on_load_click(self, event):
        self._close()

        path = self._ask_for_file()
        if path:
            self.on_load(path)

    def _on_save_as_click(self, event):
        self._close()
        self.on_save_as()

    @staticmethod
    def _ask_for_file():
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            path = filedialog.askopenfilename(
                title="Load World",
                filetypes=[("World save", "*.json"), ("All files", "*.*")],
            )
        finally:
            root.destroy()
        return path or None

    # -- lifecycle ----------------------------------------------------------

    def enable(self):
        self.manager.enable()

    def disable(self):
        self.manager.disable()

    def draw(self):
        self.manager.draw()
