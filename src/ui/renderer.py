import math

import arcade
from PIL import Image, ImageDraw

from core.substance_factory import SubstanceFactory
from simulation.body_geometry import atom_positions, body_hull, ATOM_RADIUS
from simulation.reactor import Reactor

# genome.cell_count caps mutation at MAX_CELL_COUNT, but an organism's
# actual matter.molecules count comes from real chemistry (reproduction
# reacts combined parental reserves - see Organism/OrganismFactory) and
# isn't bounded by that genetic trait. Reactor.MAX_ATOMS_PER_REACTION is
# the true worst case: a molecule can't outnumber its own atoms, so this
# many disconnected 1-atom "molecules" is the most any body can ever have.
MAX_CACHED_CELLS = Reactor.MAX_ATOMS_PER_REACTION

_TEXTURE_SIZE = 128  # pixels
_WORLD_UNITS_PER_TEXTURE = 160.0  # fixed conversion, same for every texture - comfortably fits MAX_CACHED_CELLS's worst-case extent (~52 units across) with margin, so nothing at the edge gets clipped, and keeps relative sizes between bodies meaningful

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


def _build_atom_texture(item) -> arcade.Texture:
    """One circle per atom in `item`'s body (see
    simulation.body_geometry.atom_positions), colored by element and
    blended with the item's own color. Built once at first render (see
    Renderer._get_texture, which caches by content, not per instance -
    fixed recipes like most food kinds all end up sharing one texture)."""
    positions = atom_positions(item.matter.molecules) or [(0.0, 0.0, None)]

    render_size = _TEXTURE_SIZE * _SUPERSAMPLE
    px_per_world_unit = render_size / _WORLD_UNITS_PER_TEXTURE
    center = render_size / 2
    radius_px = ATOM_RADIUS * px_per_world_unit

    image = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    for x, y, element in positions:
        # Flip y: world +y is up, image +y is down.
        px = center + x * px_per_world_unit
        py = center - y * px_per_world_unit
        element_color = SubstanceFactory.ELEMENT_COLORS.get(element, (150, 150, 220))
        color = _blend(element_color, item.color)
        draw.ellipse([px - radius_px, py - radius_px, px + radius_px, py + radius_px], fill=(*color, 255))

    image = image.resize((_TEXTURE_SIZE, _TEXTURE_SIZE), _RESAMPLE_FILTER)
    return arcade.Texture(image)


# Above this many atoms, the atom-circle layout's extra per-cell spread
# (see body_geometry.atom_positions - each molecule's own atoms fan out
# beyond the coarser CELL_TRIANGLE the physics hull actually uses) can
# visibly outgrow the hitbox by a lot. Past the threshold, fall back to a
# solid fill of the exact same hull the physics shape uses - guaranteed to
# match, at the cost of not showing individual atoms.
ATOM_RENDER_MAX_ATOMS = 10


def _build_polygon_texture(item) -> arcade.Texture:
    """Solid-filled body_hull polygon - the exact same shape used for the
    physics collision (see Substance.__init__), so there's zero visual/
    hitbox mismatch. Used once a body has more than ATOM_RENDER_MAX_ATOMS
    atoms (see _build_atom_texture)."""
    hull = body_hull(len(item.matter.molecules), scale=1.0)

    render_size = _TEXTURE_SIZE * _SUPERSAMPLE
    px_per_world_unit = render_size / _WORLD_UNITS_PER_TEXTURE
    center = render_size / 2
    points = [(center + x * px_per_world_unit, center - y * px_per_world_unit) for x, y in hull]

    image = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    ImageDraw.Draw(image).polygon(points, fill=(*item.color, 255))

    image = image.resize((_TEXTURE_SIZE, _TEXTURE_SIZE), _RESAMPLE_FILTER)
    return arcade.Texture(image)


def _build_body_texture(item) -> arcade.Texture:
    total_atoms = sum(len(molecule.atoms) for molecule in item.matter.molecules)
    if total_atoms > ATOM_RENDER_MAX_ATOMS:
        return _build_polygon_texture(item)
    return _build_atom_texture(item)


def _texture_signature(item):
    """Two items with identical body content (same atom layout, or same
    cell count once past the polygon-fallback threshold) and the same
    color render pixel-for-pixel identical textures - most food is one of
    a handful of fixed recipes (see SubstanceFactory), so this collapses
    thousands of substances down to a handful of cached textures instead
    of rebuilding one per instance (the "slow startup" bug: building a
    texture per item touched every spawned substance, thousands of them)."""
    total_atoms = sum(len(molecule.atoms) for molecule in item.matter.molecules)
    if total_atoms > ATOM_RENDER_MAX_ATOMS:
        return ("polygon", len(item.matter.molecules), tuple(item.color))

    positions = atom_positions(item.matter.molecules)
    atoms_key = tuple((round(x, 4), round(y, 4), element) for x, y, element in positions)
    return ("atoms", atoms_key, tuple(item.color))


def _build_outline_texture(cell_count: int) -> arcade.Texture:
    """Just the boundary of body_hull (the actual pymunk collision
    polygon), unfilled - shared/cached by cell_count since the debug
    overlay doesn't need per-instance atom detail, only the shape.
    Rendered into a batched SpriteList (see Renderer), not drawn with
    immediate-mode calls - hundreds of draw_polygon_outline calls a frame
    made the "Hitboxes" toggle unusably slow, independent of pause state
    since on_draw keeps running regardless of the sim thread."""
    hull = body_hull(cell_count, scale=1.0)

    render_size = _TEXTURE_SIZE * _SUPERSAMPLE
    px_per_world_unit = render_size / _WORLD_UNITS_PER_TEXTURE
    center = render_size / 2
    points = [(center + x * px_per_world_unit, center - y * px_per_world_unit) for x, y in hull]

    image = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    ImageDraw.Draw(image).polygon(points, outline=(255, 255, 255, 255), width=_SUPERSAMPLE * 2)

    image = image.resize((_TEXTURE_SIZE, _TEXTURE_SIZE), _RESAMPLE_FILTER)
    return arcade.Texture(image)


class Renderer:
    """Draws organisms/substances as sprites in a persistent SpriteList.

    A sprite is created once per entity and reused across frames (only its
    position/angle are updated); entities are added/removed incrementally
    as they appear/disappear from `items`. Rebuilding a fresh vector shape
    for every entity every frame (the previous approach) doesn't scale past
    a few hundred entities - see profiling notes in the balance/perf pass.

    Body texture shows one circle per atom (see
    simulation.body_geometry.atom_positions) built once per entity, not a
    single flat-colored silhouette - so what's drawn actually reflects what
    the body is made of. Past ATOM_RENDER_MAX_ATOMS atoms, the per-cell
    spread of that layout can visibly outgrow the coarser physics hull
    (Substance), so bigger bodies fall back to a solid fill of the exact
    same hull instead - guaranteed to match the hitbox, at the cost of
    atom-level detail (see _build_body_texture).

    Sprites also rotate to face their direction of travel - a stationary
    triangle sliding around without turning read as an inert rock rather
    than something alive.
    """

    SHAPE_SIZE = _WORLD_UNITS_PER_TEXTURE

    def __init__(self):
        self.sprite_list = arcade.SpriteList()
        self._sprites_by_id = {}

        # Reference-counted, not just cached: arcade's texture atlas has a
        # hard cap (8192 slots) and only reclaims a slot once every Python
        # reference to the Texture is gone. Content is shared across many
        # items (see _texture_signature) but each organism's exact atom
        # layout is normally unique to it, so without dropping our own
        # reference once the last item using a signature dies, textures
        # for long-dead organisms pile up forever and eventually overflow
        # the atlas on a long-running world (the crash this fixes).
        self._body_textures = {}
        self._body_texture_refcounts = {}
        self._sprite_signatures = {}

        self.show_hitboxes = False
        self.hitbox_sprite_list = arcade.SpriteList()
        self._hitbox_sprites_by_id = {}
        self._outline_textures = {}

    def _acquire_body_texture(self, item):
        signature = _texture_signature(item)
        texture = self._body_textures.get(signature)
        if texture is None:
            texture = _build_body_texture(item)
            self._body_textures[signature] = texture
            self._body_texture_refcounts[signature] = 0
        self._body_texture_refcounts[signature] += 1
        return signature, texture

    def _release_body_texture(self, signature):
        self._body_texture_refcounts[signature] -= 1
        if self._body_texture_refcounts[signature] <= 0:
            del self._body_texture_refcounts[signature]
            del self._body_textures[signature]

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
                signature, texture = self._acquire_body_texture(item)
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
                cell_count = max(1, min(len(item.matter.molecules), MAX_CACHED_CELLS))
                texture = self._outline_textures.get(cell_count)
                if texture is None:
                    texture = _build_outline_texture(cell_count)
                    self._outline_textures[cell_count] = texture

                hitbox_sprite = arcade.Sprite(texture)
                size = self.SHAPE_SIZE * item.scale
                hitbox_sprite.width = size
                hitbox_sprite.height = size
                self._hitbox_sprites_by_id[key] = hitbox_sprite
                self.hitbox_sprite_list.append(hitbox_sprite)

            # Bodies never actually rotate physically (see docstring) - the
            # outline always reflects the real, unrotated collision shape.
            hitbox_sprite.position = item.position

        stale_ids = self._sprites_by_id.keys() - seen_ids
        for key in stale_ids:
            sprite = self._sprites_by_id.pop(key)
            self.sprite_list.remove(sprite)
            self._release_body_texture(self._sprite_signatures.pop(key))

            hitbox_sprite = self._hitbox_sprites_by_id.pop(key, None)
            if hitbox_sprite is not None:
                self.hitbox_sprite_list.remove(hitbox_sprite)
