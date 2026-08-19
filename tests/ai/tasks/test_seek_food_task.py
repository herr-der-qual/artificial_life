import pymunk

from ai.tasks.seek_food_task import SeekFoodTask
from core.molecule_factory import MoleculeFactory
from simulation.elements import Elements
from simulation.genome import Genome
from simulation.matter import Matter
from simulation.organism import Organism
from simulation.substance import FOOD_KINDS


class FakeSubstance:
    def __init__(self, x, y, kind="basic"):
        self.position = pymunk.Vec2d(x, y)
        self.kind = kind


class FakeWorld:
    def __init__(self, substances):
        self.substances = substances


def make_organism(search_radius=200.0, diet=frozenset(FOOD_KINDS)):
    genome = Genome(speed=30.0, max_energy=100.0, energy_drain_rate=10.0,
                     search_radius=search_radius, wander_radius=50.0, diet=diet,
                     color=(0, 255, 0))
    matter = Matter()
    matter.add_molecule(MoleculeFactory.random_molecule([Elements.C], 2))
    return Organism(matter=matter, genome=genome)


def test_ignores_food_outside_its_own_search_radius():
    organism = make_organism(search_radius=50.0)
    world = FakeWorld([FakeSubstance(100.0, 0.0)])

    task = SeekFoodTask(organism, world)
    assert task.find_nearest_food() is None


def test_finds_food_within_its_own_search_radius():
    organism = make_organism(search_radius=150.0)
    world = FakeWorld([FakeSubstance(100.0, 0.0)])

    task = SeekFoodTask(organism, world)
    assert task.find_nearest_food() is world.substances[0]


def test_wider_genome_search_radius_sees_further():
    narrow = make_organism(search_radius=50.0)
    wide = make_organism(search_radius=150.0)
    world = FakeWorld([FakeSubstance(100.0, 0.0)])

    assert SeekFoodTask(narrow, world).find_nearest_food() is None
    assert SeekFoodTask(wide, world).find_nearest_food() is world.substances[0]


def test_ignores_food_kinds_outside_its_diet():
    organism = make_organism(diet=frozenset({"rich", "simple"}))
    world = FakeWorld([FakeSubstance(10.0, 0.0, kind="basic")])

    assert SeekFoodTask(organism, world).find_nearest_food() is None


def test_targets_food_kinds_within_its_diet():
    organism = make_organism(diet=frozenset({"basic"}))
    world = FakeWorld([FakeSubstance(10.0, 0.0, kind="basic")])

    assert SeekFoodTask(organism, world).find_nearest_food() is world.substances[0]


def test_skips_disliked_food_in_favor_of_a_farther_accepted_one():
    organism = make_organism(diet=frozenset({"simple"}))
    disliked_but_closer = FakeSubstance(5.0, 0.0, kind="basic")
    accepted_but_farther = FakeSubstance(40.0, 0.0, kind="simple")
    world = FakeWorld([disliked_but_closer, accepted_but_farther])

    assert SeekFoodTask(organism, world).find_nearest_food() is accepted_but_farther
