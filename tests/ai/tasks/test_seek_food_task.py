import pymunk

from ai.tasks.seek_food_task import SeekFoodTask
from core.molecule_factory import MoleculeFactory
from simulation.elements import Elements
from simulation.genome import Genome
from simulation.matter import Matter
from simulation.organism import Organism


class FakeSubstance:
    def __init__(self, x, y):
        self.position = pymunk.Vec2d(x, y)


class FakeWorld:
    def __init__(self, substances):
        self.substances = substances


def make_organism(search_radius):
    genome = Genome(speed=30.0, max_energy=100.0, energy_drain_rate=10.0,
                     search_radius=search_radius, color=(0, 255, 0))
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
