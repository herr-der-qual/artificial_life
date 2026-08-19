import tkinter as tk
from tkinter import filedialog

import arcade
import arcade.gui


class SaveAsDialog:
    """Centered popup for Save As: a name field and a folder picked via a
    native browse dialog. Confirms via on_confirm(directory, name)."""

    WIDTH = 380
    ROW_HEIGHT = 28
    PATH_DISPLAY_MAX_LEN = 34

    def __init__(self, on_confirm, default_directory=None):
        self.on_confirm = on_confirm
        self.selected_directory = default_directory

        self.manager = arcade.gui.UIManager()
        self.is_open = False

        self._build_widgets()
        self._place_initial()

    def _build_widgets(self):
        self.name_input = arcade.gui.UIInputText(text="Untitled World", width=220, height=26)
        self.path_label = arcade.gui.UILabel(text=self._path_display(), width=220)

        browse_button = arcade.gui.UIFlatButton(text="Browse...", width=90, height=self.ROW_HEIGHT)
        browse_button.on_click = self._on_browse_click

        save_button = arcade.gui.UIFlatButton(text="Save", width=90, height=self.ROW_HEIGHT)
        save_button.on_click = self._on_save_click

        cancel_button = arcade.gui.UIFlatButton(text="Cancel", width=90, height=self.ROW_HEIGHT)
        cancel_button.on_click = self._on_cancel_click

        name_row = arcade.gui.UIBoxLayout(vertical=False, space_between=8)
        name_row.add(arcade.gui.UILabel(text="Name:", width=45))
        name_row.add(self.name_input)

        path_row = arcade.gui.UIBoxLayout(vertical=False, space_between=8)
        path_row.add(arcade.gui.UILabel(text="Path:", width=45))
        path_row.add(self.path_label)
        path_row.add(browse_button)

        button_row = arcade.gui.UIBoxLayout(vertical=False, space_between=10)
        button_row.add(save_button)
        button_row.add(cancel_button)

        stack = arcade.gui.UIBoxLayout(vertical=True, align="left", space_between=10)
        stack.add(arcade.gui.UILabel(text="Save World As", width=300, font_size=14, bold=True))
        stack.add(name_row)
        stack.add(path_row)
        stack.add(button_row)

        self.panel = arcade.gui.UIBoxLayout(vertical=False, space_between=0)
        self.panel.with_padding(all=14)
        self.panel.with_background(color=arcade.types.Color(25, 25, 25, 245))
        self.panel.add(stack)
        self.panel.fit_content()
        self.panel.rect = self.panel.rect.resize(width=self.WIDTH)
        self.panel.visible = False

        self.manager.add(self.panel)

    def _place_initial(self):
        window = self.manager.window
        self.panel.rect = self.panel.rect.align_center((window.width / 2, window.height / 2))

    def _path_display(self):
        if not self.selected_directory:
            return "(choose a folder)"

        text = str(self.selected_directory)
        if len(text) <= self.PATH_DISPLAY_MAX_LEN:
            return text
        return "..." + text[-(self.PATH_DISPLAY_MAX_LEN - 3):]

    def open(self, default_name):
        self.name_input.text = default_name
        self.is_open = True
        self.panel.visible = True

    def _close(self):
        self.is_open = False
        self.panel.visible = False

    def _on_browse_click(self, event):
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            directory = filedialog.askdirectory(title="Choose folder to save the world in")
        finally:
            root.destroy()

        if directory:
            self.selected_directory = directory
            self.path_label.text = self._path_display()

    def _on_save_click(self, event):
        name = self.name_input.text.strip()
        if not name or not self.selected_directory:
            return

        self._close()
        self.on_confirm(self.selected_directory, name)

    def _on_cancel_click(self, event):
        self._close()

    # -- lifecycle ----------------------------------------------------------

    def enable(self):
        self.manager.enable()

    def disable(self):
        self.manager.disable()

    def draw(self):
        self.manager.draw()
