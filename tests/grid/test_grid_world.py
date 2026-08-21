from core.molecule_factory import MoleculeFactory
from simulation.matter import Matter

from src_grid.core.world_config import WorldConfig
from src_grid.core.food_factory import FoodFactory
from src_grid.simulation.world import World
from src_grid.simulation.organism import Organism


def make_config(tmp_path, **overrides):
    config = WorldConfig(path=tmp_path / "grid_world_config.json")
    config.data.update(overrides)
    return config


def test_spawns_the_requested_amount_of_food(tmp_path):
    world = World(make_config(tmp_path, width=10, height=10, food_count=15, organism_count=0))
    assert len(world.grid) == 15


def test_food_positions_are_all_unique(tmp_path):
    world = World(make_config(tmp_path, width=10, height=10, food_count=15, organism_count=0))
    positions = [food.position for food in world.grid]
    assert len(set(positions)) == len(positions)


def test_never_spawns_more_food_than_cells_exist(tmp_path):
    """Regression target: asking for more food than the grid has room for
    must not hang forever looking for a free cell."""
    world = World(make_config(tmp_path, width=3, height=3, food_count=100, organism_count=0))
    assert len(world.grid) == 9


def test_spawns_the_requested_amount_of_organisms(tmp_path):
    world = World(make_config(tmp_path, width=10, height=10, food_count=0, organism_count=12))
    assert len(world.organisms) == 12
    assert all(isinstance(o, Organism) for o in world.organisms)
    assert len(world.grid) == 12


def test_food_and_organisms_never_share_a_cell(tmp_path):
    world = World(make_config(tmp_path, width=10, height=10, food_count=30, organism_count=30))
    positions = [entity.position for entity in world.grid]
    assert len(set(positions)) == len(positions)
    assert len(world.grid) == 60


def test_update_moves_at_least_one_organism_over_many_ticks(tmp_path):
    """A single tick can be a no-op (blocked move, or the unlucky random
    direction picks off the edge) - across many ticks, on an otherwise
    empty field, organisms should clearly have moved somewhere. Kept well
    under starvation range (MAX_ENERGY / ENERGY_DRAIN_PER_TICK = 50 ticks)
    so the population is still fully alive to compare positions against."""
    world = World(make_config(tmp_path, width=20, height=20, food_count=0, organism_count=5))
    starting_positions = [o.position for o in world.organisms]

    for _ in range(20):
        world.update()

    ending_positions = [o.position for o in world.organisms]
    assert ending_positions != starting_positions


def test_update_never_lets_two_organisms_collide(tmp_path):
    world = World(make_config(tmp_path, width=20, height=20, food_count=0, organism_count=15))

    for _ in range(20):
        world.update()
        positions = [o.position for o in world.organisms]
        assert len(set(positions)) == len(positions)


def test_organisms_starve_and_get_removed_once_energy_runs_out(tmp_path):
    world = World(make_config(tmp_path, width=20, height=20, food_count=0, organism_count=5))
    ticks_to_starve = int(Organism.MAX_ENERGY / Organism.ENERGY_DRAIN_PER_TICK)

    for _ in range(ticks_to_starve):
        world.update()

    assert world.organisms == []
    # The cells aren't empty - each death left a corpse behind (see below).
    assert len(world.grid) == 5
    assert world.deaths_count == 5


def test_death_leaves_a_corpse_made_of_the_organisms_own_matter(tmp_path):
    world = World(make_config(tmp_path, width=10, height=10, food_count=0, organism_count=0))
    organism = Organism(_simple_matter(), color=(0, 0, 0), energy=Organism.ENERGY_DRAIN_PER_TICK)
    world.grid.place(organism, 4, 4)
    world.organisms.append(organism)
    original_matter = organism.matter

    world.update()

    assert world.organisms == []
    corpse = world.grid.occupant_at(4, 4)
    assert corpse is not None
    assert corpse.kind == "corpse"
    assert corpse.matter is original_matter
    assert corpse.color == world.CORPSE_COLOR


def test_eating_food_is_counted_and_removes_it_from_the_grid(tmp_path):
    """Organism.step() scans all 4 neighbors for food before falling back
    to a random direction, so a single adjacent food is always found and
    eaten - deterministic, no retry loop needed."""
    world = World(make_config(tmp_path, width=20, height=20, food_count=0, organism_count=0))
    organism = Organism(_simple_matter(), color=(0, 0, 0))
    organism.reproduction_cooldown = 999  # isolate this test from reproduction
    world.grid.place(organism, 5, 5)
    world.organisms.append(organism)
    world.grid.place(FoodFactory.create_random(), 6, 5)

    world.update()

    assert world.food_eaten_count == 1
    assert len(world.grid) == 1
    assert organism.position == (6, 5)


def _simple_matter() -> Matter:
    matter = Matter()
    matter.add_molecule(MoleculeFactory.simple_organic())
    return matter


def _ready_to_reproduce() -> Organism:
    organism = Organism(_simple_matter(), color=(0, 0, 0), energy=Organism.MAX_ENERGY)
    while organism.reserve.mass < Organism.REPRODUCE_MATTER_THRESHOLD:
        organism.reserve.add_molecule(MoleculeFactory.simple_organic())
    return organism


def test_eligible_organism_reproduces_into_a_free_neighbor_cell(tmp_path):
    world = World(make_config(tmp_path, width=10, height=10, food_count=0, organism_count=0))
    parent = _ready_to_reproduce()
    world.grid.place(parent, 5, 5)
    world.organisms.append(parent)

    world.update()

    assert len(world.organisms) == 2
    assert world.births_count == 1
    assert world.max_generation_reached == 1
    child = next(o for o in world.organisms if o is not parent)
    assert child.generation == 1
    # A direct neighbor of wherever the parent ended up this tick (it may
    # have moved before reproducing - step() runs before _try_reproduce).
    pcol, prow = parent.position
    ccol, crow = child.position
    assert abs(ccol - pcol) + abs(crow - prow) == 1


def test_reproduction_is_skipped_with_no_free_neighbor_cell(tmp_path):
    """A 1x1 grid has no neighbor cells at all (every direction is out of
    bounds) - an otherwise-eligible parent simply can't reproduce, and
    doesn't pay the cost trying."""
    world = World(make_config(tmp_path, width=1, height=1, food_count=0, organism_count=0))
    parent = _ready_to_reproduce()
    world.grid.place(parent, 0, 0)
    world.organisms.append(parent)

    energy_before, reserve_before = parent.energy, parent.reserve.mass
    world.update()

    assert len(world.organisms) == 1
    assert world.births_count == 0
    assert parent.energy == energy_before - Organism.ENERGY_DRAIN_PER_TICK
    assert parent.reserve.mass == reserve_before


def test_tick_count_starts_at_zero_and_increments_on_update(tmp_path):
    world = World(make_config(tmp_path, width=10, height=10, food_count=0, organism_count=1))
    assert world.tick_count == 0

    world.update()
    world.update()
    world.update()

    assert world.tick_count == 3
