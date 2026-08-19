import pytest

from simulation.body_geometry import body_hull, cell_offsets, CELL_TRIANGLE


def test_single_cell_hull_matches_the_classic_triangle():
    """cell_count=1 must render/collide pixel-for-pixel identical to the
    original single-triangle shape this project has always used."""
    hull = body_hull(1, scale=1.0)
    assert set(hull) == set(CELL_TRIANGLE)


def test_single_cell_hull_scales_uniformly():
    hull = body_hull(1, scale=2.0)
    expected = {(x * 2.0, y * 2.0) for x, y in CELL_TRIANGLE}
    assert set(hull) == expected


def test_hull_extent_grows_with_cell_count():
    def max_extent(count):
        hull = body_hull(count, scale=1.0)
        return max(max(abs(x), abs(y)) for x, y in hull)

    extents = [max_extent(n) for n in (1, 2, 3, 5, 8)]
    assert extents == sorted(extents)
    assert extents[0] < extents[-1]


def test_hull_is_convex():
    """pymunk.Poly requires a convex polygon - verify the cross product of
    consecutive edges never changes sign (allowing for collinear points)."""
    hull = body_hull(6, scale=1.0)
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


def test_cell_offsets_single_cell_is_at_origin():
    assert cell_offsets(1) == [(0.0, 0.0)]


def test_cell_offsets_are_unique_and_spread_out():
    offsets = cell_offsets(8)
    assert len(offsets) == 8
    assert len(set(offsets)) == 8


def test_body_hull_treats_non_positive_count_as_one_cell():
    assert set(body_hull(0, scale=1.0)) == set(CELL_TRIANGLE)
