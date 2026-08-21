import pytest

from src_grid.simulation.grid import Grid


class FakeEntity:
    def __init__(self):
        self.position = None


def test_new_grid_is_empty():
    grid = Grid(5, 5)
    assert len(grid) == 0
    assert grid.is_free(0, 0)


def test_place_sets_the_entitys_position():
    grid = Grid(5, 5)
    entity = FakeEntity()

    grid.place(entity, 2, 3)

    assert entity.position == (2, 3)
    assert grid.occupant_at(2, 3) is entity
    assert len(grid) == 1


def test_place_on_an_occupied_cell_raises():
    grid = Grid(5, 5)
    grid.place(FakeEntity(), 1, 1)

    with pytest.raises(ValueError):
        grid.place(FakeEntity(), 1, 1)


def test_place_out_of_bounds_raises():
    grid = Grid(5, 5)
    with pytest.raises(ValueError):
        grid.place(FakeEntity(), 5, 0)  # width=5 -> valid cols are 0..4
    with pytest.raises(ValueError):
        grid.place(FakeEntity(), -1, 0)


def test_is_free_is_false_outside_bounds():
    grid = Grid(5, 5)
    assert not grid.is_free(5, 0)
    assert not grid.is_free(0, -1)


def test_remove_frees_the_cell():
    grid = Grid(5, 5)
    entity = FakeEntity()
    grid.place(entity, 2, 2)

    grid.remove(entity)

    assert grid.is_free(2, 2)
    assert grid.occupant_at(2, 2) is None
    assert len(grid) == 0


def test_move_relocates_to_a_free_cell():
    grid = Grid(5, 5)
    entity = FakeEntity()
    grid.place(entity, 0, 0)

    moved = grid.move(entity, 1, 1)

    assert moved is True
    assert entity.position == (1, 1)
    assert grid.is_free(0, 0)
    assert grid.occupant_at(1, 1) is entity


def test_move_into_an_occupied_cell_fails_and_leaves_both_entities_put():
    grid = Grid(5, 5)
    a = FakeEntity()
    b = FakeEntity()
    grid.place(a, 0, 0)
    grid.place(b, 1, 0)

    moved = grid.move(a, 1, 0)

    assert moved is False
    assert a.position == (0, 0)
    assert b.position == (1, 0)
    assert grid.occupant_at(0, 0) is a
    assert grid.occupant_at(1, 0) is b


def test_move_out_of_bounds_fails():
    grid = Grid(5, 5)
    entity = FakeEntity()
    grid.place(entity, 0, 0)

    assert grid.move(entity, -1, 0) is False
    assert entity.position == (0, 0)


def test_iterating_the_grid_yields_all_occupants():
    grid = Grid(5, 5)
    a, b, c = FakeEntity(), FakeEntity(), FakeEntity()
    grid.place(a, 0, 0)
    grid.place(b, 1, 1)
    grid.place(c, 2, 2)

    assert set(grid) == {a, b, c}


def test_nearby_positions_finds_occupants_within_radius():
    grid = Grid(20, 20)
    grid.place(FakeEntity(), 10, 10)
    grid.place(FakeEntity(), 12, 10)  # 2 away - within radius 3
    grid.place(FakeEntity(), 10, 18)  # far - outside radius 3

    found = set(grid.nearby_positions(10, 10, 3))

    assert found == {(10, 10), (12, 10)}


def test_nearby_positions_respects_a_bucket_boundary():
    """The two positions land in different buckets (BUCKET_SIZE=8) - the
    index has to check neighboring buckets too, not just the query
    point's own bucket."""
    grid = Grid(20, 20)
    grid.place(FakeEntity(), 7, 7)   # bucket (0, 0)
    grid.place(FakeEntity(), 8, 7)   # bucket (1, 0) - adjacent cell, different bucket

    found = set(grid.nearby_positions(7, 7, 2))

    assert found == {(7, 7), (8, 7)}


def test_nearby_positions_index_stays_correct_after_remove_and_move():
    grid = Grid(20, 20)
    a = FakeEntity()
    b = FakeEntity()
    grid.place(a, 5, 5)
    grid.place(b, 6, 5)

    grid.remove(a)
    assert (5, 5) not in set(grid.nearby_positions(5, 5, 3))

    grid.move(b, 9, 9)  # jumps to a different bucket
    assert set(grid.nearby_positions(9, 9, 1)) == {(9, 9)}
    assert (6, 5) not in set(grid.nearby_positions(6, 5, 3))


def test_nearby_positions_empty_buckets_are_pruned():
    """Not observable through the public API directly, but an unbounded
    _buckets dict full of empty sets would be a slow, silent leak on a
    long-running world with lots of turnover (spawns/deaths/moves) - make
    sure vacated buckets are actually dropped, not just emptied."""
    grid = Grid(20, 20)
    entity = FakeEntity()
    grid.place(entity, 5, 5)
    grid.remove(entity)

    assert grid._buckets == {}
