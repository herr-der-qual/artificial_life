import pymunk

from ai.tasks.seek_food_task import SeekFoodTask
from ai.tasks.seek_mate_task import SeekMateTask
from ai.tasks.waypoint_task import WaypointTask
from core.molecule_factory import MoleculeFactory
from simulation.elements import Elements
from simulation.genome import Genome
from simulation.matter import Matter
from simulation.organism import Organism


class FakeSubstance:
    """Enough of a Substance for SeekFoodTask.do() to run: a position."""

    def __init__(self, x=50.0, y=50.0):
        self.position = pymunk.Vec2d(x, y)


class FakeWorld:
    def __init__(self, substances=None, organisms=None):
        self.substances = substances if substances is not None else []
        self.organisms = organisms if organisms is not None else []


def make_organism(energy_ratio=1.0, fertile=False, max_energy=200.0):
    genome = Genome(speed=30.0, max_energy=max_energy, energy_drain_rate=10.0, search_radius=200.0, color=(0, 255, 0))
    matter = Matter()
    matter.add_molecule(MoleculeFactory.random_molecule([Elements.C], 2))

    organism = Organism(matter=matter, genome=genome)
    organism.energy = max_energy * energy_ratio

    if fertile:
        while organism.reserve.mass < Organism.REPRODUCE_MATTER_THRESHOLD:
            extra = Matter()
            extra.add_molecule(MoleculeFactory.simple_organic())
            organism.digest(extra)

    return organism


def test_hunger_takes_priority_over_mating():
    organism = make_organism(energy_ratio=0.1, fertile=True)
    organism.brain.world = FakeWorld(substances=[FakeSubstance()], organisms=[organism])

    organism.brain.update()

    assert isinstance(organism.brain.tasks[0], SeekFoodTask)


def test_mating_pursued_when_not_hungry():
    organism = make_organism(energy_ratio=1.0, fertile=True)
    mate = make_organism(energy_ratio=1.0, fertile=True)
    mate.position = (50.0, 50.0)

    organism.brain.world = FakeWorld(substances=[FakeSubstance()], organisms=[organism, mate])

    organism.brain.update()

    assert isinstance(organism.brain.tasks[0], SeekMateTask)


def test_wanders_when_no_goal_is_active():
    organism = make_organism(energy_ratio=1.0, fertile=False)
    organism.brain.world = FakeWorld(substances=[], organisms=[])

    organism.brain.update()

    assert isinstance(organism.brain.tasks[0], WaypointTask)


def test_does_not_restart_the_same_goal_task_every_tick():
    organism = make_organism(energy_ratio=0.1, fertile=False)
    organism.brain.world = FakeWorld(substances=[FakeSubstance()], organisms=[])

    organism.brain.update()
    first_task = organism.brain.tasks[0]

    organism.brain.update()
    assert organism.brain.tasks[0] is first_task
