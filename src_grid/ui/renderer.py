import arcade
from PIL import Image, ImageDraw

from core.substance_factory import SubstanceFactory
from simulation.body_geometry import atom_positions, ATOM_RADIUS

CELL_PIXELS = 32  # on-screen size of one grid cell

# Grid food is always small (a handful of atoms), unlike ui.renderer's
# _build_body_texture (calibrated to also fit much bigger multicellular
# bodies) - reusing that calibration here would shrink food down to a
# barely-visible speck within its cell. Tight, grid-appropriate canvas
# instead, sized to comfortably fit a ~6-atom molecule.
_TEXTURE_SIZE = 64
_WORLD_UNITS_PER_TEXTURE = 12.0
_SUPERSAMPLE = 2  # supersample + BOX downsample so atom circles read as
_RESAMPLE_FILTER = Image.Resampling.BOX  # circles, not blocky squares (see ui.renderer for the full story)
ELEMENT_COLOR_WEIGHT = 0.55


def _blend(element_color, item_color) -> tuple:
    return tuple(
        round(element_color[i] * ELEMENT_COLOR_WEIGHT + item_color[i] * (1 - ELEMENT_COLOR_WEIGHT))
        for i in range(3)
    )


def _build_food_texture(food) -> arcade.Texture:
    """One circle per atom (see simulation.body_geometry.atom_positions),
    colored by element and blended with the food's own color - same idea
    as ui.renderer._build_body_texture, just recalibrated for grid-sized
    food instead of arbitrarily large bodies."""
    positions = atom_positions(food.matter.molecules) or [(0.0, 0.0, None)]

    render_size = _TEXTURE_SIZE * _SUPERSAMPLE
    px_per_world_unit = render_size / _WORLD_UNITS_PER_TEXTURE
    center = render_size / 2
    radius_px = ATOM_RADIUS * px_per_world_unit

    image = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    for x, y, element in positions:
        px = center + x * px_per_world_unit
        py = center - y * px_per_world_unit  # flip: world +y is up, image +y is down
        element_color = SubstanceFactory.ELEMENT_COLORS.get(element, (150, 150, 220))
        color = _blend(element_color, food.color)
        draw.ellipse([px - radius_px, py - radius_px, px + radius_px, py + radius_px], fill=(*color, 255))

    image = image.resize((_TEXTURE_SIZE, _TEXTURE_SIZE), _RESAMPLE_FILTER)
    return arcade.Texture(image)


class Renderer:
    """Draws a Grid's occupants as sprites in a persistent SpriteList -
    same reasoning as ui.renderer.Renderer (rebuilding shapes every frame
    doesn't scale). Textures are cached by content (element layout +
    color), not per instance - most food is one of a handful of fixed
    recipes (see FoodFactory), so this stays a handful of textures
    regardless of how much food is on the field."""

    def __init__(self):
        self.sprite_list = arcade.SpriteList()
        self._sprites_by_id = {}
        self._textures = {}

        self.show_grid = False
        self._grid_line_cache = None  # ((width, height), point_list) - rebuilt only if the grid size changes

    def _texture_for(self, food) -> arcade.Texture:
        positions = atom_positions(food.matter.molecules)
        signature = (
            tuple((round(x, 4), round(y, 4), element) for x, y, element in positions),
            tuple(food.color),
        )
        texture = self._textures.get(signature)
        if texture is None:
            texture = _build_food_texture(food)
            self._textures[signature] = texture
        return texture

    def render(self, grid):
        seen_ids = set()

        for entity in grid:
            key = id(entity)
            seen_ids.add(key)

            sprite = self._sprites_by_id.get(key)
            if sprite is None:
                sprite = arcade.Sprite(self._texture_for(entity))
                sprite.width = CELL_PIXELS
                sprite.height = CELL_PIXELS
                self._sprites_by_id[key] = sprite
                self.sprite_list.append(sprite)

            col, row = entity.position
            sprite.position = (col * CELL_PIXELS + CELL_PIXELS / 2, row * CELL_PIXELS + CELL_PIXELS / 2)

        stale_ids = self._sprites_by_id.keys() - seen_ids
        for key in stale_ids:
            self.sprite_list.remove(self._sprites_by_id.pop(key))

        self.sprite_list.draw()

        if self.show_grid:
            self._draw_grid_lines(grid)

    def _draw_grid_lines(self, grid):
        cache_key = (grid.width, grid.height)
        if self._grid_line_cache is None or self._grid_line_cache[0] != cache_key:
            self._grid_line_cache = (cache_key, self._build_grid_line_points(grid))

        _, points = self._grid_line_cache
        arcade.draw_lines(points, (70, 70, 70, 255), 1)

    @staticmethod
    def _build_grid_line_points(grid) -> list:
        """Just the cell dividers (grid.width+1 vertical + grid.height+1
        horizontal lines) - a fixed, small count independent of how much
        is actually on the field, so plain immediate-mode drawing is fine
        here (unlike per-entity hitboxes, which needed batching)."""
        width_px = grid.width * CELL_PIXELS
        height_px = grid.height * CELL_PIXELS

        points = []
        for col in range(grid.width + 1):
            x = col * CELL_PIXELS
            points.append((x, 0))
            points.append((x, height_px))
        for row in range(grid.height + 1):
            y = row * CELL_PIXELS
            points.append((0, y))
            points.append((width_px, y))
        return points
