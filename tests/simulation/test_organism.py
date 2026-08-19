import pytest

from simulation.elements import Elements
from simulation.genome import Genome
from simulation.matter import Matter
from simulation.organism import Organism
from simulation.substance import FOOD_KINDS
from core.molecule_factory import MoleculeFactory


def make_simple_organism(**genome_overrides):
    defaults = dict(
        speed=30.0, max_energy=100.0, energy_drain_rate=10.0,
        search_radius=200.0, wander_radius=50.0, cell_count=1,
        diet=frozenset(FOOD_KINDS), color=(0, 255, 0),
    )
    defaults.update(genome_overrides)
    genome = Genome(**defaults)

    matter = Matter()
    matter.add_molecule(MoleculeFactory.random_molecule([Elements.C], 2))

    return Organism(matter=matter, genome=genome)


def test_starting_energy_defaults_to_max_energy():
    organism = make_simple_organism(max_energy=80.0)
    assert organism.energy == 80.0


def test_search_radius_comes_from_genome():
    organism = make_simple_organism(search_radius=123.0)
    assert organism.search_radius == 123.0


def test_wander_radius_and_diet_come_from_genome():
    diet = frozenset({"basic", "simple"})
    organism = make_simple_organism(wander_radius=77.0, diet=diet)
    assert organism.wander_radius == 77.0
    assert organism.diet == diet


def test_starting_energy_can_be_overridden():
    genome = Genome(
        speed=30, max_energy=100, energy_drain_rate=10, search_radius=200,
        wander_radius=50, cell_count=1, diet=frozenset(FOOD_KINDS), color=(0, 255, 0),
    )
    matter = Matter()
    matter.add_molecule(MoleculeFactory.random_molecule([Elements.C], 2))

    organism = Organism(matter=matter, genome=genome, starting_energy=25.0)
    assert organism.energy == 25.0


def test_die_sets_energy_to_zero_and_marks_dead():
    organism = make_simple_organism()
    organism.die()
    assert not organism.is_alive
    assert organism.energy == 0


def test_update_after_death_is_a_no_op():
    organism = make_simple_organism()
    organism.die()
    organism.update(1.0)
    assert organism.energy == 0


def test_digest_stashes_products_into_reserve():
    organism = make_simple_organism()
    assert organism.reserve.mass == 0

    food = MoleculeFactory.simple_organic()
    food_matter = Matter()
    food_matter.add_molecule(food)

    organism.digest(food_matter)

    assert organism.reserve.mass == pytest.approx(food.mass)


def test_cannot_reproduce_without_enough_energy_or_reserve():
    organism = make_simple_organism(max_energy=100.0)
    organism.energy = 100.0
    assert not organism.can_reproduce()  # no reserve yet


def test_can_reproduce_once_energy_and_reserve_thresholds_are_met():
    organism = make_simple_organism(max_energy=200.0)
    organism.energy = 200.0

    while organism.reserve.mass < Organism.REPRODUCE_MATTER_THRESHOLD:
        extra = Matter()
        extra.add_molecule(MoleculeFactory.simple_organic())
        organism.digest(extra)

    assert organism.can_reproduce()


def test_reproduction_cooldown_blocks_and_then_expires():
    organism = make_simple_organism(max_energy=200.0)
    organism.energy = 200.0
    organism.reproduction_cooldown = 5.0

    while organism.reserve.mass < Organism.REPRODUCE_MATTER_THRESHOLD:
        extra = Matter()
        extra.add_molecule(MoleculeFactory.simple_organic())
        organism.digest(extra)

    assert not organism.can_reproduce()

    organism.reproduction_cooldown = 0.0
    assert organism.can_reproduce()


def test_cannot_reproduce_asexually_without_enough_energy_or_reserve():
    organism = make_simple_organism(max_energy=100.0)
    organism.energy = 100.0
    assert not organism.can_reproduce_asexually()  # no reserve yet


def test_can_reproduce_asexually_once_energy_and_reserve_thresholds_are_met():
    organism = make_simple_organism(max_energy=400.0)
    organism.energy = 400.0

    while organism.reserve.mass < Organism.ASEXUAL_MATTER_THRESHOLD:
        extra = Matter()
        extra.add_molecule(MoleculeFactory.simple_organic())
        organism.digest(extra)

    assert organism.can_reproduce_asexually()


def test_sexual_eligibility_alone_is_not_enough_for_asexual_budding():
    """Asexual budding needs roughly double what one sexual parent needs
    (see Organism.ASEXUAL_ENERGY_COST/ASEXUAL_MATTER_THRESHOLD) - meeting
    only the (lower) sexual bar must not also unlock solo reproduction."""
    organism = make_simple_organism(max_energy=200.0)
    organism.energy = 200.0

    while organism.reserve.mass < Organism.REPRODUCE_MATTER_THRESHOLD:
        extra = Matter()
        extra.add_molecule(MoleculeFactory.simple_organic())
        organism.digest(extra)

    assert organism.can_reproduce()
    assert not organism.can_reproduce_asexually()
