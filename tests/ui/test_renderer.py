from core.molecule_factory import MoleculeFactory
from simulation.matter import Matter
from simulation.substance import Substance
from simulation.body_geometry import body_hull
import ui.renderer as renderer_module
from ui.renderer import Renderer


def make_water_substance():
    matter = Matter()
    matter.add_molecule(MoleculeFactory.water())
    return Substance(matter, color=(70, 130, 220), kind="simple")


def test_items_with_identical_content_share_one_cached_body_texture():
    renderer = Renderer()
    a = make_water_substance()
    b = make_water_substance()

    renderer._sync([a, b])

    assert len(renderer._body_cache) == 1
    assert renderer._sprites_by_id[id(a)].texture is renderer._sprites_by_id[id(b)].texture


def test_body_texture_is_evicted_once_its_last_user_is_removed():
    """Regression target: arcade's texture atlas has a hard cap (8192
    slots), only reclaimed once every Python reference to a Texture is
    gone. Without dropping our own cache reference when nothing uses a
    signature anymore, textures for organisms that died hours ago pile up
    forever and eventually overflow the atlas."""
    renderer = Renderer()
    item = make_water_substance()

    renderer._sync([item])
    assert len(renderer._body_cache) == 1

    renderer._sync([])  # item no longer present -> its sprite is stale
    assert len(renderer._body_cache) == 0
    assert len(renderer._body_cache._refcounts) == 0


def test_shared_body_texture_survives_while_at_least_one_user_remains():
    renderer = Renderer()
    a = make_water_substance()
    b = make_water_substance()

    renderer._sync([a, b])
    renderer._sync([b])  # a is gone, b still uses the shared texture

    assert len(renderer._body_cache) == 1

    renderer._sync([])
    assert len(renderer._body_cache) == 0


def test_hitbox_outline_texture_is_also_evicted_once_unused():
    renderer = Renderer()
    item = make_water_substance()

    renderer._sync([item])
    assert len(renderer._outline_cache) == 1

    renderer._sync([])
    assert len(renderer._outline_cache) == 0
    assert len(renderer._outline_cache._refcounts) == 0


def test_hitbox_texture_is_shared_across_items_with_the_same_shape_regardless_of_color():
    """The outline is colorless, so two items with the same atom layout
    but different colors should still share one cached outline texture -
    more reuse than the (color-sensitive) body texture cache gets."""
    renderer = Renderer()
    a = make_water_substance()
    b = make_water_substance()
    b.color = (255, 0, 0)  # different color, same shape

    renderer._sync([a, b])

    assert len(renderer._body_cache) == 2  # different color -> different body texture
    assert len(renderer._outline_cache) == 1  # same shape -> shared outline texture


def test_build_outline_texture_uses_the_same_hull_as_the_physics_shape():
    """Regression target: the outline used to be cached by a coarse
    cell-count key with its own approximate hull, which could disagree
    with the physics shape (and the atom-circle render) for bodies whose
    real chemistry didn't match their nominal cell count. Now both are
    built from body_hull(item.matter.molecules), so they can't drift
    apart."""
    item = make_water_substance()

    outline_texture = renderer_module._build_outline_texture(item)
    expected_hull = body_hull(item.matter.molecules, scale=1.0)

    assert outline_texture is not None
    assert set(item.shape.get_vertices()) == set(expected_hull)
