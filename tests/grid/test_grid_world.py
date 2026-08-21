from src_grid.simulation.world import World
from src_grid.simulation.organism import Organism


def test_spawns_the_requested_amount_of_food():
    world = World(width=10, height=10, food_count=15, organism_count=0)
    assert len(world.grid) == 15


def test_food_positions_are_all_unique():
    world = World(width=10, height=10, food_count=15, organism_count=0)
    positions = [food.position for food in world.grid]
    assert len(set(positions)) == len(positions)


def test_never_spawns_more_food_than_cells_exist():
    """Regression target: asking for more food than the grid has room for
    must not hang forever looking for a free cell."""
    world = World(width=3, height=3, food_count=100, organism_count=0)
    assert len(world.grid) == 9


def test_spawns_the_requested_amount_of_organisms():
    world = World(width=10, height=10, food_count=0, organism_count=12)
    assert len(world.organisms) == 12
    assert all(isinstance(o, Organism) for o in world.organisms)
    assert len(world.grid) == 12


def test_food_and_organisms_never_share_a_cell():
    world = World(width=10, height=10, food_count=30, organism_count=30)
    positions = [entity.position for entity in world.grid]
    assert len(set(positions)) == len(positions)
    assert len(world.grid) == 60


def test_update_moves_at_least_one_organism_over_many_ticks():
    """A single tick can be a no-op (blocked move, or the unlucky random
    direction picks off the edge) - across many ticks, on an otherwise
    empty field, organisms should clearly have moved somewhere."""
    world = World(width=20, height=20, food_count=0, organism_count=5)
    starting_positions = [o.position for o in world.organisms]

    for _ in range(50):
        world.update()

    ending_positions = [o.position for o in world.organisms]
    assert ending_positions != starting_positions


def test_update_never_lets_two_organisms_collide():
    world = World(width=20, height=20, food_count=0, organism_count=15)

    for _ in range(50):
        world.update()
        positions = [o.position for o in world.organisms]
        assert len(set(positions)) == len(positions)
