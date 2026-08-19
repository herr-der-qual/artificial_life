import pytest

from core.molecule_factory import MoleculeFactory
from core.organism_factory import OrganismFactory
from simulation.elements import Elements
from simulation.genome import Genome
from simulation.matter import Matter
from simulation.organism import Organism


def make_fertile_organism(x=0.0, y=0.0):
    genome = Genome(speed=30.0, max_energy=200.0, energy_drain_rate=10.0, search_radius=200.0, color=(0, 255, 0))
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
    a.genome = Genome(speed=10.0, max_energy=200.0, energy_drain_rate=5.0, search_radius=200.0, color=(0, 0, 0))
    b.genome = Genome(speed=90.0, max_energy=200.0, energy_drain_rate=25.0, search_radius=200.0, color=(255, 255, 255))

    child = OrganismFactory.create_offspring(a, b)

    # mutation jitters the value but crossover always starts from one parent's pick
    assert 10.0 * 0.85 <= child.genome.speed <= 90.0 * 1.15
    assert 5.0 * 0.85 <= child.genome.energy_drain_rate <= 25.0 * 1.15
