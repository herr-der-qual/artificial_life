import arcade

CELL_PIXELS = 32  # on-screen size of one grid cell


class Renderer:
    """Draws a Grid's occupants as sprites in a persistent SpriteList -
    same reasoning as ui.renderer.Renderer (rebuilding shapes every frame
    doesn't scale). Every occupant is one flat-colored square filling its
    cell - one cell is one organism/food item, full stop (multicellular
    bodies made of several cells are a separate, later feature - not this
    grid's concern yet).

    Uses arcade.SpriteSolidColor rather than a custom per-item texture:
    arcade internally shares a single texture for every (width, height)
    pair and applies each sprite's color as a tint, so there's no
    per-content texture cache to manage (and no way to overflow the
    texture atlas the way the old atom-cluster renderer could - see git
    history for that whole saga)."""

    def __init__(self):
        self.sprite_list = arcade.SpriteList()
        self._sprites_by_id = {}

        self.show_grid = False
        self._grid_line_cache = None  # ((width, height), point_list) - rebuilt only if the grid size changes

    def render(self, grid):
        seen_ids = set()

        for entity in grid:
            key = id(entity)
            seen_ids.add(key)

            sprite = self._sprites_by_id.get(key)
            if sprite is None:
                sprite = arcade.SpriteSolidColor(CELL_PIXELS, CELL_PIXELS, color=entity.color)
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
