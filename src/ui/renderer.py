import math

import arcade
from PIL import Image, ImageDraw

from core.substance_factory import SubstanceFactory
from simulation.body_geometry import atom_positions, body_hull, ATOM_RADIUS

_TEXTURE_SIZE = 128  # pixels
_WORLD_UNITS_PER_TEXTURE = 160.0  # fixed conversion, same for every texture - comfortably fits even a very large body with margin, and keeps relative sizes between bodies meaningful

# PIL's ImageDraw has no antialiasing - a ~3px-radius circle drawn directly
# comes out as a blocky little square, not round. Draw at a higher
# resolution and downsample (a standard supersampling antialiasing trick)
# so atom circles actually read as circles. BOX (plain area-average) is
# the appropriate filter for this - it IS what supersampling means - and
# is far cheaper than LANCZOS, which was most of the cost of building a
# texture (profiled: ~2.4ms/texture at SS4+LANCZOS vs ~0.3ms at SS2+BOX -
# building thousands of them at world startup was the "slow launch" bug).
_SUPERSAMPLE = 2
_RESAMPLE_FILTER = Image.Resampling.BOX

# How much of an atom's circle color comes from its element (vs. the
# organism/substance's own color) - enough to read the body's real
# composition at a glance, without losing the color as an identity signal
# (it's a mutating genome trait) or breaking "all food reads as blue".
ELEMENT_COLOR_WEIGHT = 0.55


def _blend(element_color, item_color) -> tuple:
    return tuple(
        round(element_color[i] * ELEMENT_COLOR_WEIGHT + item_color[i] * (1 - ELEMENT_COLOR_WEIGHT))
        for i in range(3)
    )


def _project(points, render_size) -> list:
    px_per_world_unit = render_size / _WORLD_UNITS_PER_TEXTURE
    center = render_size / 2
    # Flip y: world +y is up, image +y is down.
    return [(center + x * px_per_world_unit, center - y * px_per_world_unit) for x, y in points]


def _build_body_texture(item) -> arcade.Texture:
    """One circle per atom in `item`'s body (see
    simulation.body_geometry.atom_positions), colored by element and
    blended with the item's own color - the same atom positions
    body_hull hulls for the physics shape (Substance), so what's drawn
    always reflects (and stays within) what's actually collided with.
    Built once per distinct body (see Renderer, which caches by content,
    not per instance - fixed recipes like most food kinds all end up
    sharing one texture)."""
    positions = atom_positions(item.matter.molecules) or [(0.0, 0.0, None)]
    elements = [element for _, _, element in positions]

    render_size = _TEXTURE_SIZE * _SUPERSAMPLE
    radius_px = ATOM_RADIUS * (render_size / _WORLD_UNITS_PER_TEXTURE)

    image = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    projected = _project([(x, y) for x, y, _ in positions], render_size)
    for (px, py), element in zip(projected, elements):
        element_color = SubstanceFactory.ELEMENT_COLORS.get(element, (150, 150, 220))
        color = _blend(element_color, item.color)
        draw.ellipse([px - radius_px, py - radius_px, px + radius_px, py + radius_px], fill=(*color, 255))

    image = image.resize((_TEXTURE_SIZE, _TEXTURE_SIZE), _RESAMPLE_FILTER)
    return arcade.Texture(image)


def _texture_signature(item):
    """Two items with identical atom layout and color render pixel-for-
    pixel identical textures - most food is one of a handful of fixed
    recipes (see SubstanceFactory), so this collapses thousands of
    substances down to a handful of cached textures instead of rebuilding
    one per instance (the "slow startup" bug: building a texture per item
    touched every spawned substance, thousands of them)."""
    return (_hull_signature(item), tuple(item.color))


def _hull_signature(item):
    """The geometric part of an item's body - atom positions only, no
    color. Two items with the same shape share the same physics-matching
    hull outline regardless of their (possibly different) color."""
    positions = atom_positions(item.matter.molecules)
    return tuple((round(x, 4), round(y, 4)) for x, y, _ in positions)


def _build_outline_texture(item) -> arcade.Texture:
    """Just the boundary of body_hull (the actual pymunk collision
    polygon), unfilled. Rendered into a batched SpriteList (see
    Renderer), not drawn with immediate-mode calls - hundreds of
    draw_polygon_outline calls a frame made the "Hitboxes" toggle
    unusably slow, independent of pause state since on_draw keeps
    running regardless of the sim thread."""
    hull = body_hull(item.matter.molecules, scale=1.0)

    render_size = _TEXTURE_SIZE * _SUPERSAMPLE
    points = _project(hull, render_size)

    image = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    ImageDraw.Draw(image).polygon(points, outline=(255, 255, 255, 255), width=_SUPERSAMPLE * 2)

    image = image.resize((_TEXTURE_SIZE, _TEXTURE_SIZE), _RESAMPLE_FILTER)
    return arcade.Texture(image)


class _TextureCache:
    """Reference-counted texture cache, shared logic for both the body and
    hitbox-outline caches below. Reference-counted, not just cached:
    arcade's texture atlas has a hard cap (8192 slots) and only reclaims a
    slot once every Python reference to the Texture is gone. Content is
    shared across many items (see _texture_signature/_hull_signature) but
    each organism's exact atom layout is normally unique to it, so without
    dropping our own reference once the last item using a signature dies,
    textures for long-dead organisms pile up forever and eventually
    overflow the atlas on a long-running world (the crash this fixes)."""

    def __init__(self, build, signature):
        self._build = build
        self._signature = signature
        self._textures = {}
        self._refcounts = {}

    def acquire(self, item):
        signature = self._signature(item)
        texture = self._textures.get(signature)
        if texture is None:
            texture = self._build(item)
            self._textures[signature] = texture
            self._refcounts[signature] = 0
        self._refcounts[signature] += 1
        return signature, texture

    def release(self, signature):
        self._refcounts[signature] -= 1
        if self._refcounts[signature] <= 0:
            del self._refcounts[signature]
            del self._textures[signature]

    def __len__(self):
        return len(self._textures)


class Renderer:
    """Draws organisms/substances as sprites in a persistent SpriteList.

    A sprite is created once per entity and reused across frames (only its
    position/angle are updated); entities are added/removed incrementally
    as they appear/disappear from `items`. Rebuilding a fresh vector shape
    for every entity every frame (the previous approach) doesn't scale past
    a few hundred entities - see profiling notes in the balance/perf pass.

    Body texture shows one circle per atom (see
    simulation.body_geometry.atom_positions), and the physics hull
    (Substance) is the convex hull of those same atoms - so the two always
    match by construction, whatever the body's actual composition.

    Sprites also rotate to face their direction of travel - a stationary
    triangle sliding around without turning read as an inert rock rather
    than something alive.
    """

    SHAPE_SIZE = _WORLD_UNITS_PER_TEXTURE

    def __init__(self):
        self.sprite_list = arcade.SpriteList()
        self._sprites_by_id = {}
        self._body_cache = _TextureCache(_build_body_texture, _texture_signature)
        self._sprite_signatures = {}

        self.show_hitboxes = False
        self.hitbox_sprite_list = arcade.SpriteList()
        self._hitbox_sprites_by_id = {}
        self._outline_cache = _TextureCache(_build_outline_texture, _hull_signature)
        self._hitbox_sprite_signatures = {}

    def render(self, items):
        self._sync(items)
        self.sprite_list.draw()
        if self.show_hitboxes:
            self.hitbox_sprite_list.draw()

    def _sync(self, items):
        seen_ids = set()

        for item in items:
            key = id(item)
            seen_ids.add(key)

            sprite = self._sprites_by_id.get(key)
            if sprite is None:
                signature, texture = self._body_cache.acquire(item)
                sprite = arcade.Sprite(texture)
                size = self.SHAPE_SIZE * item.scale
                sprite.width = size
                sprite.height = size
                self._sprites_by_id[key] = sprite
                self._sprite_signatures[key] = signature
                self.sprite_list.append(sprite)

            sprite.position = item.position

            vx, vy = item.velocity
            if vx * vx + vy * vy > 1e-6:
                sprite.angle = math.degrees(math.atan2(vx, vy))

            hitbox_sprite = self._hitbox_sprites_by_id.get(key)
            if hitbox_sprite is None:
                hitbox_signature, hitbox_texture = self._outline_cache.acquire(item)
                hitbox_sprite = arcade.Sprite(hitbox_texture)
                size = self.SHAPE_SIZE * item.scale
                hitbox_sprite.width = size
                hitbox_sprite.height = size
                self._hitbox_sprites_by_id[key] = hitbox_sprite
                self._hitbox_sprite_signatures[key] = hitbox_signature
                self.hitbox_sprite_list.append(hitbox_sprite)

            # Bodies never actually rotate physically (see docstring) - the
            # outline always reflects the real, unrotated collision shape.
            hitbox_sprite.position = item.position

        stale_ids = self._sprites_by_id.keys() - seen_ids
        for key in stale_ids:
            sprite = self._sprites_by_id.pop(key)
            self.sprite_list.remove(sprite)
            self._body_cache.release(self._sprite_signatures.pop(key))

            hitbox_sprite = self._hitbox_sprites_by_id.pop(key, None)
            if hitbox_sprite is not None:
                self.hitbox_sprite_list.remove(hitbox_sprite)
                self._outline_cache.release(self._hitbox_sprite_signatures.pop(key))
