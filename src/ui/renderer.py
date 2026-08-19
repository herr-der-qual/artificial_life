import arcade
from PIL import Image, ImageDraw


def _build_triangle_texture(size: int = 32) -> arcade.Texture:
    """A single triangle matching the world-space shape [(-4,-4),(0,4),(4,-4)]
    used by Organism/Substance, rasterized once and reused (tinted per
    instance via Sprite.color) instead of building per-entity vector shapes."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.polygon([(0, size), (size / 2, 0), (size, size)], fill=(255, 255, 255, 255))
    return arcade.Texture(image)


class Renderer:
    """Draws organisms/substances as sprites in a persistent SpriteList.

    A sprite is created once per entity and reused across frames (only its
    position/color are updated); entities are added/removed incrementally
    as they appear/disappear from `items`. Rebuilding a fresh vector shape
    for every entity every frame (the previous approach) doesn't scale past
    a few hundred entities - see profiling notes in the balance/perf pass.
    """

    SHAPE_SIZE = 8  # world units, matches the original triangle's bounding box

    def __init__(self):
        self.sprite_list = arcade.SpriteList()
        self._texture = _build_triangle_texture()
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
                sprite = arcade.Sprite(self._texture)
                sprite.width = self.SHAPE_SIZE
                sprite.height = self.SHAPE_SIZE
                self._sprites_by_id[key] = sprite
                self.sprite_list.append(sprite)

            sprite.position = item.position
            sprite.color = item.color

        stale_ids = self._sprites_by_id.keys() - seen_ids
        for key in stale_ids:
            sprite = self._sprites_by_id.pop(key)
            self.sprite_list.remove(sprite)
