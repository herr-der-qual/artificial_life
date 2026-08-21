from core.molecule_factory import MoleculeFactory
from simulation.matter import Matter

from src_grid.simulation.grid import Grid
from src_grid.simulation.food import Food
from src_grid.simulation.genome import Genome
from src_grid.simulation.organism import Organism
from src_grid.core.organism_factory import OrganismFactory


def _genome(color=(0, 0, 0), max_energy=100.0, energy_drain_rate=2.0) -> Genome:
    return Genome(max_energy=max_energy, energy_drain_rate=energy_drain_rate, color=color)


def test_step_moves_to_an_adjacent_cell_or_stays_put():
    grid = Grid(10, 10)
    organism = OrganismFactory.create_random()
    grid.place(organism, 5, 5)

    organism.step(grid)

    col, row = organism.position
    distance = abs(col - 5) + abs(row - 5)
    assert distance in (0, 1)  # 0 if the random direction happened to be blocked (edge case, not here)


def test_step_never_moves_onto_an_occupied_cell():
    grid = Grid(3, 3)
    mover = OrganismFactory.create_random()
    grid.place(mover, 1, 1)

    # surround the mover on all 4 sides so every possible step is blocked
    blockers = [OrganismFactory.create_random() for _ in range(4)]
    for blocker, (col, row) in zip(blockers, [(2, 1), (0, 1), (1, 2), (1, 0)]):
        grid.place(blocker, col, row)

    for _ in range(20):
        mover.step(grid)

    assert mover.position == (1, 1)
    for blocker, expected in zip(blockers, [(2, 1), (0, 1), (1, 2), (1, 0)]):
        assert blocker.position == expected


def _bare_matter() -> Matter:
    matter = Matter()
    matter.add_molecule(MoleculeFactory.simple_organic())
    return matter


def test_step_drains_energy():
    grid = Grid(5, 5)
    organism = Organism(_bare_matter(), _genome())
    grid.place(organism, 2, 2)

    organism.step(grid)

    assert organism.energy == organism.max_energy - organism.energy_drain_rate


def test_organism_starves_once_energy_runs_out():
    grid = Grid(5, 5)
    organism = Organism(_bare_matter(), _genome(), energy=2.0)
    grid.place(organism, 2, 2)

    ate = organism.step(grid)

    assert ate is False
    assert organism.is_alive is False
    assert organism.energy <= 0


def test_step_eats_adjacent_food_and_gains_energy():
    grid = Grid(5, 5)
    organism = Organism(_bare_matter(), _genome(), energy=10.0)
    grid.place(organism, 2, 2)
    food = Food(_bare_matter(), color=(0, 0, 0), kind="rich")
    grid.place(food, 3, 2)

    ate = organism.step(grid)

    assert ate is True
    assert organism.position == (3, 2)
    assert grid.occupant_at(3, 2) is organism
    # Food is gone from the grid, not just displaced.
    assert all(not isinstance(entity, Food) for entity in grid)


def test_eating_stashes_leftover_atoms_in_reserve():
    grid = Grid(5, 5)
    organism = Organism(_bare_matter(), _genome(), energy=10.0)
    grid.place(organism, 2, 2)
    grid.place(Food(_bare_matter(), color=(0, 0, 0), kind="rich"), 3, 2)

    organism.step(grid)

    assert organism.reserve.mass > 0


def _fill_reserve(organism: Organism):
    while organism.reserve.mass < Organism.REPRODUCE_MATTER_THRESHOLD:
        organism.reserve.add_molecule(MoleculeFactory.simple_organic())


def test_cannot_reproduce_without_enough_energy():
    organism = Organism(_bare_matter(), _genome(), energy=1.0)
    _fill_reserve(organism)

    assert organism.can_reproduce() is False


def test_cannot_reproduce_without_enough_reserve():
    organism = Organism(_bare_matter(), _genome(), energy=100.0)

    assert organism.can_reproduce() is False


def test_cannot_reproduce_while_on_cooldown():
    organism = Organism(_bare_matter(), _genome(), energy=100.0)
    _fill_reserve(organism)
    organism.reproduction_cooldown = 5

    assert organism.can_reproduce() is False


def test_can_reproduce_with_enough_energy_and_reserve():
    organism = Organism(_bare_matter(), _genome(), energy=100.0)
    _fill_reserve(organism)

    assert organism.can_reproduce() is True


def test_create_offspring_asexual_charges_the_parent_and_returns_a_child():
    parent = Organism(_bare_matter(), _genome(color=(220, 220, 80)), energy=100.0, generation=2)
    _fill_reserve(parent)

    child = OrganismFactory.create_offspring_asexual(parent)

    assert child is not None
    assert child.generation == 3
    assert child.is_alive is True
    assert parent.energy == 100.0 - Organism.REPRODUCE_ENERGY_COST
    assert parent.reproduction_cooldown == Organism.REPRODUCE_COOLDOWN
    assert parent.reserve.mass == 0  # spent building the child


def test_create_offspring_asexual_inherits_and_mutates_the_parents_genome():
    parent = Organism(_bare_matter(), _genome(color=(220, 220, 80)), energy=100.0)
    _fill_reserve(parent)

    child = OrganismFactory.create_offspring_asexual(parent)

    assert child.genome is not parent.genome
    # mutate() jitters every field - vanishingly unlikely to land on the
    # exact same tuple/float again, so "different" is the real assertion.
    assert child.max_energy != parent.max_energy or child.energy_drain_rate != parent.energy_drain_rate


def test_create_offspring_asexual_refuses_an_ineligible_parent():
    parent = Organism(_bare_matter(), _genome(), energy=1.0)

    assert OrganismFactory.create_offspring_asexual(parent) is None
