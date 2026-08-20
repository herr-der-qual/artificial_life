from core.molecule_factory import MoleculeFactory
from simulation.elements import Elements
from simulation.matter import Matter
from simulation.substance import Substance
import ui.renderer as renderer_module
from ui.renderer import Renderer


class FakeItem:
    def __init__(self, matter, color=(100, 150, 220)):
        self.matter = matter
        self.color = color


def make_item(atom_count):
    matter = Matter()
    matter.add_molecule(MoleculeFactory.random_molecule([Elements.C], atom_count))
    return FakeItem(matter)


def test_dispatches_to_atom_circles_under_the_threshold(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(renderer_module, "_build_atom_texture", lambda item: sentinel)
    monkeypatch.setattr(renderer_module, "_build_polygon_texture", lambda item: "should not be called")

    item = make_item(renderer_module.ATOM_RENDER_MAX_ATOMS)

    assert renderer_module._build_body_texture(item) is sentinel


def test_dispatches_to_solid_polygon_over_the_threshold(monkeypatch):
    """Regression target: past the threshold, the atom-circle layout's
    extra per-cell spread visibly outgrew the (coarser) physics hitbox -
    fall back to filling that exact hull instead, guaranteed to match."""
    sentinel = object()
    monkeypatch.setattr(renderer_module, "_build_polygon_texture", lambda item: sentinel)
    monkeypatch.setattr(renderer_module, "_build_atom_texture", lambda item: "should not be called")

    item = make_item(renderer_module.ATOM_RENDER_MAX_ATOMS + 1)

    assert renderer_module._build_body_texture(item) is sentinel


def make_water_substance():
    matter = Matter()
    matter.add_molecule(MoleculeFactory.water())
    return Substance(matter, color=(70, 130, 220), kind="simple")


def test_items_with_identical_content_share_one_cached_texture():
    renderer = Renderer()
    a = make_water_substance()
    b = make_water_substance()

    renderer._sync([a, b])

    assert len(renderer._body_textures) == 1
    assert renderer._sprites_by_id[id(a)].texture is renderer._sprites_by_id[id(b)].texture


def test_texture_is_evicted_once_its_last_user_is_removed():
    """Regression target: arcade's texture atlas has a hard cap (8192
    slots), only reclaimed once every Python reference to a Texture is
    gone. Without dropping our own cache reference when nothing uses a
    signature anymore, textures for organisms that died hours ago pile up
    forever and eventually overflow the atlas."""
    renderer = Renderer()
    item = make_water_substance()

    renderer._sync([item])
    assert len(renderer._body_textures) == 1

    renderer._sync([])  # item no longer present -> its sprite is stale
    assert len(renderer._body_textures) == 0
    assert len(renderer._body_texture_refcounts) == 0


def test_shared_texture_survives_while_at_least_one_user_remains():
    renderer = Renderer()
    a = make_water_substance()
    b = make_water_substance()

    renderer._sync([a, b])
    renderer._sync([b])  # a is gone, b still uses the shared texture

    assert len(renderer._body_textures) == 1

    renderer._sync([])
    assert len(renderer._body_textures) == 0
