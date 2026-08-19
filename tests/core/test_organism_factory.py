import pytest

from core.molecule_factory import MoleculeFactory
from core.organism_factory import OrganismFactory
from simulation.elements import Elements
from simulation.genome import Genome, SEXUAL_MUTATION_RATE
from simulation.matter import Matter
from simulation.organism import Organism
from simulation.substance import FOOD_KINDS


def make_fertile_organism(x=0.0, y=0.0):
    genome = Genome(
        speed=30.0, max_energy=200.0, energy_drain_rate=10.0, search_radius=200.0,
        wander_radius=50.0, cell_count=1, diet=frozenset(FOOD_KINDS), color=(0, 255, 0),
    )
    matter = Matter()
    matter.add_molecule(MoleculeFactory.random_molecule([Elements.C], 2))

    organism = Organism(matter=matter, genome=genome)
    organism.position = (x, y)
    organism.energy = 200.0

    while organism.reserve.mass < Organism.REPRODUCE_MATTER_THRESHOLD:
        extra = Matter()
        extra.add_molecule(MoleculeFactory.simple_organic())
        organism.digest(extra)

    return organism


def make_solo_fertile_organism(x=0.0, y=0.0):
    """Meets the (higher) asexual budding threshold on its own - see
    Organism.ASEXUAL_ENERGY_COST/ASEXUAL_MATTER_THRESHOLD."""
    genome = Genome(
        speed=30.0, max_energy=400.0, energy_drain_rate=10.0, search_radius=200.0,
        wander_radius=50.0, cell_count=1, diet=frozenset(FOOD_KINDS), color=(0, 255, 0),
    )
    matter = Matter()
    matter.add_molecule(MoleculeFactory.random_molecule([Elements.C], 2))

    organism = Organism(matter=matter, genome=genome)
    organism.position = (x, y)
    organism.energy = 400.0

    while organism.reserve.mass < Organism.ASEXUAL_MATTER_THRESHOLD:
        extra = Matter()
        extra.add_molecule(MoleculeFactory.simple_organic())
        organism.digest(extra)

    return organism


def test_create_random_produces_a_valid_organism():
    organism = OrganismFactory.create_random()
    assert organism.matter.mass > 0
    assert organism.energy == organism.max_energy


def test_create_offspring_returns_none_if_a_parent_is_not_eligible():
    fertile = make_fertile_organism()
    infertile = make_fertile_organism()
    infertile.reserve = Matter()  # spend it back down below threshold

    assert OrganismFactory.create_offspring(fertile, infertile) is None
    # parents must not be charged for a reproduction that didn't happen
    assert fertile.energy == 200.0


def test_create_offspring_charges_both_parents_and_sets_cooldown():
    a = make_fertile_organism()
    b = make_fertile_organism()

    child = OrganismFactory.create_offspring(a, b)

    assert child is not None
    assert a.energy == pytest.approx(200.0 - Organism.REPRODUCE_ENERGY_COST)
    assert b.energy == pytest.approx(200.0 - Organism.REPRODUCE_ENERGY_COST)
    assert a.reproduction_cooldown == Organism.REPRODUCE_COOLDOWN
    assert b.reproduction_cooldown == Organism.REPRODUCE_COOLDOWN
    assert a.reserve.mass == 0
    assert b.reserve.mass == 0


def test_create_offspring_conserves_mass_from_parents_reserves():
    a = make_fertile_organism()
    b = make_fertile_organism()
    spent_mass = a.reserve.mass + b.reserve.mass

    child = OrganismFactory.create_offspring(a, b)

    assert child.matter.mass == pytest.approx(spent_mass)


def test_create_offspring_positions_child_at_parents_midpoint():
    a = make_fertile_organism(x=0.0, y=0.0)
    b = make_fertile_organism(x=100.0, y=40.0)

    child = OrganismFactory.create_offspring(a, b)

    assert child.position.x == pytest.approx(50.0)
    assert child.position.y == pytest.approx(20.0)


def test_create_offspring_inherits_traits_from_one_of_the_parents_lineage():
    a = make_fertile_organism()
    b = make_fertile_organism()
    a.genome = Genome(
        speed=10.0, max_energy=200.0, energy_drain_rate=5.0, search_radius=200.0,
        wander_radius=50.0, cell_count=1, diet=frozenset(FOOD_KINDS), color=(0, 0, 0),
    )
    b.genome = Genome(
        speed=90.0, max_energy=200.0, energy_drain_rate=25.0, search_radius=200.0,
        wander_radius=50.0, cell_count=1, diet=frozenset(FOOD_KINDS), color=(255, 255, 255),
    )

    child = OrganismFactory.create_offspring(a, b)

    # crossover always starts from one parent's pick; sexual reproduction
    # then jitters it at SEXUAL_MUTATION_RATE (a deliberately strong bonus
    # over asexual budding's base rate, see genome.py).
    rate = SEXUAL_MUTATION_RATE
    assert 10.0 * (1 - rate) <= child.genome.speed <= 90.0 * (1 + rate)
    assert 5.0 * (1 - rate) <= child.genome.energy_drain_rate <= 25.0 * (1 + rate)


def test_create_offspring_asexual_returns_none_if_parent_is_not_eligible():
    infertile = make_fertile_organism()  # meets sexual, not asexual, threshold

    assert OrganismFactory.create_offspring_asexual(infertile) is None
    assert infertile.energy == 200.0


def test_create_offspring_asexual_charges_parent_alone_and_sets_cooldown():
    parent = make_solo_fertile_organism()
    spent_mass = parent.reserve.mass

    child = OrganismFactory.create_offspring_asexual(parent)

    assert child is not None
    assert parent.energy == pytest.approx(400.0 - Organism.ASEXUAL_ENERGY_COST)
    assert parent.reproduction_cooldown == Organism.REPRODUCE_COOLDOWN
    assert parent.reserve.mass == 0
    assert child.matter.mass == pytest.approx(spent_mass)
    assert child.generation == parent.generation + 1
    assert child.position.x == pytest.approx(parent.position.x)
    assert child.position.y == pytest.approx(parent.position.y)


def test_create_offspring_asexual_mutates_at_base_rate_not_sexual_bonus():
    parent = make_solo_fertile_organism()
    parent.genome = Genome(
        speed=50.0, max_energy=400.0, energy_drain_rate=10.0, search_radius=200.0,
        wander_radius=50.0, cell_count=1, diet=frozenset(FOOD_KINDS), color=(0, 255, 0),
    )

    for _ in range(50):
        # re-fill reserve each time since create_offspring_asexual spends it
        while parent.reserve.mass < Organism.ASEXUAL_MATTER_THRESHOLD:
            extra = Matter()
            extra.add_molecule(MoleculeFactory.simple_organic())
            parent.digest(extra)
        parent.reproduction_cooldown = 0.0
        parent.energy = 400.0

        child = OrganismFactory.create_offspring_asexual(parent)

        # base mutation jitter (BASE_MUTATION_RATE, well under the sexual
        # bonus) - never as wide as the sexual-reproduction test's bound.
        assert 50.0 * 0.7 <= child.genome.speed <= 50.0 * 1.3
