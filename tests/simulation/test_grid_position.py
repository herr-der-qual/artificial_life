import math

import pytest

from simulation.world import grid_position


def test_positions_stay_within_bounds():
    bound = 100.0
    count = 37

    for i in range(count):
        x, y = grid_position(i, count, bound)
        assert -bound <= x <= bound
        assert -bound <= y <= bound


def test_positions_are_unique():
    count = 50
    positions = {grid_position(i, count, 200.0) for i in range(count)}
    assert len(positions) == count


def test_single_organism_spawns_at_center():
    assert grid_position(0, 1, 300.0) == pytest.approx((0.0, 0.0))


def test_minimum_spacing_exceeds_organism_shape_size():
    """Regression target: random placement could stack organisms almost on
    top of each other. A grid should keep neighbours farther apart than the
    ~8-unit triangle shape, so they don't spawn already overlapping."""
    bound = 500.0
    count = 100
    positions = [grid_position(i, count, bound) for i in range(count)]

    columns = math.ceil(math.sqrt(count))
    expected_cell_width = (2 * bound) / columns
    assert expected_cell_width > 8

    # neighbouring cells (adjacent column) are exactly one cell width apart
    assert positions[1][0] - positions[0][0] == pytest.approx(expected_cell_width)


def test_covers_a_large_count_without_error():
    bound = 6000.0
    count = 40000
    positions = [grid_position(i, count, bound) for i in range(count)]
    assert len(set(positions)) == count
