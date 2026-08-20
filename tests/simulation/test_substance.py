import pytest

from core.molecule_factory import MoleculeFactory
from simulation.body_geometry import body_hull
from simulation.matter import Matter
from simulation.substance import Substance


def make_matter(molecule_count):
    matter = Matter()
    for _ in range(molecule_count):
        matter.add_molecule(MoleculeFactory.water())
    return matter


def test_single_molecule_shape_matches_body_hull_of_its_own_matter():
    matter = make_matter(1)
    substance = Substance(matter, color=(0, 0, 255))

    vertices = set(substance.shape.get_vertices())
    assert vertices == set(body_hull(matter.molecules, scale=1.0))


def test_multi_molecule_shape_has_more_vertices_and_a_bigger_footprint():
    single = Substance(make_matter(1), color=(0, 0, 255))
    multi = Substance(make_matter(5), color=(0, 0, 255))

    single_extent = max(max(abs(v.x), abs(v.y)) for v in single.shape.get_vertices())
    multi_extent = max(max(abs(v.x), abs(v.y)) for v in multi.shape.get_vertices())

    assert multi_extent > single_extent


def test_shape_scale_still_multiplies_the_whole_body():
    unscaled = Substance(make_matter(1), color=(0, 0, 255), scale=1.0)
    scaled = Substance(make_matter(1), color=(0, 0, 255), scale=2.0)

    unscaled_extent = max(max(abs(v.x), abs(v.y)) for v in unscaled.shape.get_vertices())
    scaled_extent = max(max(abs(v.x), abs(v.y)) for v in scaled.shape.get_vertices())

    assert scaled_extent == pytest.approx(unscaled_extent * 2.0)
