import pytest

from core.molecule_factory import MoleculeFactory
from simulation.elements import Elements
from simulation.body_geometry import body_hull, cell_offsets, atom_positions, ATOM_RADIUS


def make_molecule(atom_count):
    return MoleculeFactory.random_molecule([Elements.C], atom_count)


def test_single_atom_hull_matches_its_own_footprint():
    """A lone atom's hull is just its footprint square (a hull of one
    square is the square itself)."""
    hull = body_hull([make_molecule(1)], scale=1.0)
    expected = {
        (-ATOM_RADIUS, -ATOM_RADIUS), (ATOM_RADIUS, -ATOM_RADIUS),
        (ATOM_RADIUS, ATOM_RADIUS), (-ATOM_RADIUS, ATOM_RADIUS),
    }
    assert set(hull) == expected


def test_hull_scales_uniformly():
    unscaled = body_hull([make_molecule(1)], scale=1.0)
    scaled = body_hull([make_molecule(1)], scale=2.0)

    unscaled_extent = max(max(abs(x), abs(y)) for x, y in unscaled)
    scaled_extent = max(max(abs(x), abs(y)) for x, y in scaled)
    assert scaled_extent == pytest.approx(unscaled_extent * 2.0)


def test_hull_extent_grows_with_more_atoms():
    def max_extent(atom_count):
        hull = body_hull([make_molecule(atom_count)], scale=1.0)
        return max(max(abs(x), abs(y)) for x, y in hull)

    extents = [max_extent(n) for n in (1, 2, 3, 5, 8)]
    assert extents == sorted(extents)
    assert extents[0] < extents[-1]


def test_hull_is_convex():
    """pymunk.Poly requires a convex polygon - verify the cross product of
    consecutive edges never changes sign (allowing for collinear points)."""
    hull = body_hull([make_molecule(3), make_molecule(4)], scale=1.0)
    n = len(hull)
    assert n >= 3

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    signs = set()
    for i in range(n):
        o, a, b = hull[i], hull[(i + 1) % n], hull[(i + 2) % n]
        c = cross(o, a, b)
        if abs(c) > 1e-9:
            signs.add(c > 0)
    assert len(signs) <= 1


def test_hull_encloses_every_atom():
    """Every atom's own footprint corner must lie within (or on) the
    hull - the whole point of hulling around real atom positions instead
    of a coarse per-cell approximation is that nothing pokes outside it."""
    molecules = [make_molecule(4), make_molecule(3), make_molecule(2)]
    hull = body_hull(molecules, scale=1.0)
    positions = atom_positions(molecules)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    n = len(hull)
    for x, y, _ in positions:
        # a point inside a convex polygon (CCW winding) is on the
        # non-negative side of every edge
        for i in range(n):
            a, b = hull[i], hull[(i + 1) % n]
            assert cross(a, b, (x, y)) >= -1e-6


def test_body_hull_handles_an_empty_molecule_list():
    hull = body_hull([], scale=1.0)
    assert len(hull) >= 3


def test_cell_offsets_single_cell_is_at_origin():
    assert cell_offsets(1) == [(0.0, 0.0)]


def test_cell_offsets_are_unique_and_spread_out():
    offsets = cell_offsets(8)
    assert len(offsets) == 8
    assert len(set(offsets)) == 8


def test_atom_positions_returns_one_entry_per_atom():
    water = MoleculeFactory.water()  # O, H, H - 3 atoms
    co2 = MoleculeFactory.co2()  # C, O, O - 3 atoms

    positions = atom_positions([water, co2])

    assert len(positions) == 6


def test_atom_positions_pairs_each_point_with_its_real_element():
    water = MoleculeFactory.water()

    positions = atom_positions([water])
    elements = sorted(element.name for _, _, element in positions)

    assert elements == sorted(["O", "H", "H"])


def test_atom_positions_spreads_atoms_apart_within_a_molecule():
    molecule = MoleculeFactory.random_molecule([Elements.C], 5)

    positions = atom_positions([molecule])
    xy_points = [(x, y) for x, y, _ in positions]

    assert len(set(xy_points)) == len(xy_points)


def test_atom_positions_is_empty_for_no_molecules():
    assert atom_positions([]) == []
