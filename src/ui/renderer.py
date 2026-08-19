import arcade
from PIL import Image, ImageDraw

from simulation.body_geometry import body_hull
from simulation.genome import MAX_CELL_COUNT

# A little above MAX_CELL_COUNT: genome.cell_count caps mutation there, but
# an organism's actual matter.molecules count (what body_hull renders) is
# driven by real chemistry - e.g. reproduction reacting parental reserves -
# and isn't strictly bounded by the genetic trait. Cache textures generously
# past the genetic cap rather than let an unusual body fall back silently.
MAX_CACHED_CELLS = MAX_CELL_COUNT + 4

_TEXTURE_SIZE = 160  # pixels
_WORLD_UNITS_PER_TEXTURE = 40.0  # fixed conversion, same for every cached texture (comfortably fits MAX_CACHED_CELLS's hull) - so relative sizes are preserved between them


def _build_body_texture(cell_count: int) -> arcade.Texture:
    """Rasterizes the exact same hull Substance uses for its physics shape
    (see simulation.body_geometry.body_hull) - same fixed world-to-pixel
    scale for every cell_count, so a bigger body actually fills more of its
    texture rather than being independently re-normalized to look the same
    size as a smaller one."""
    hull = body_hull(cell_count, scale=1.0)

    px_per_world_unit = _TEXTURE_SIZE / _WORLD_UNITS_PER_TEXTURE
    center = _TEXTURE_SIZE / 2
    # Flip y: world +y is up, image +y is down.
    points = [(center + x * px_per_world_unit, center - y * px_per_world_unit) for x, y in hull]

    image = Image.new("RGBA", (_TEXTURE_SIZE, _TEXTURE_SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(image).polygon(points, fill=(255, 255, 255, 255))
    return arcade.Texture(image)


class Renderer:
    """Draws organisms/substances as sprites in a persistent SpriteList.

    A sprite is created once per entity and reused across frames (only its
    position/color are updated); entities are added/removed incrementally
    as they appear/disappear from `items`. Rebuilding a fresh vector shape
    for every entity every frame (the previous approach) doesn't scale past
    a few hundred entities - see profiling notes in the balance/perf pass.

    Body silhouette is one of a small set of precomputed textures keyed by
    cell count (len(item.matter.molecules)) - the same hull polygon backs
    both this texture and the item's physics shape (see Substance), so what
    gets drawn always matches what actually collides.
    """

    # World-units span of the full texture canvas (_WORLD_UNITS_PER_TEXTURE)
    # scaled onto screen - a single-cell body's texture is a small triangle
    # within that canvas, same as the original 8-unit triangle always was.
    SHAPE_SIZE = _WORLD_UNITS_PER_TEXTURE

    def __init__(self):
        self.sprite_list = arcade.SpriteList()
        self._textures = {n: _build_body_texture(n) for n in range(1, MAX_CACHED_CELLS + 1)}
        self._sprites_by_id = {}

    def render(self, items):
        self._sync(items)
        self.sprite_list.draw()

    def _sync(self, items):
        seen_ids = set()

        for item in items:
            key = id(item)
            seen_ids.add(key)

            sprite = self._sprites_by_id.get(key)
            if sprite is None:
                cell_count = min(len(item.matter.molecules), MAX_CACHED_CELLS)
                sprite = arcade.Sprite(self._textures[max(1, cell_count)])
                size = self.SHAPE_SIZE * item.scale
                sprite.width = size
                sprite.height = size
                self._sprites_by_id[key] = sprite
                self.sprite_list.append(sprite)

            sprite.position = item.position
            sprite.color = item.color

        stale_ids = self._sprites_by_id.keys() - seen_ids
        for key in stale_ids:
            sprite = self._sprites_by_id.pop(key)
            self.sprite_list.remove(sprite)
