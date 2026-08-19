from core.molecule_factory import MoleculeFactory
from simulation.elements import Elements
from simulation.genome import Genome
from simulation.matter import Matter
from simulation.organism import Organism
from simulation.substance import Substance
from simulation.world import World


class FakeShape:
    def __init__(self, body, collision_type):
        self.body = body
        self.collision_type = collision_type


class FakeArbiter:
    def __init__(self, shape_a, shape_b):
        self.shapes = (shape_a, shape_b)


def make_organism(x=0.0, y=0.0, max_energy=200.0, fertile=False):
    genome = Genome(speed=30.0, max_energy=max_energy, energy_drain_rate=10.0,
                     search_radius=200.0, color=(0, 255, 0))
    matter = Matter()
    matter.add_molecule(MoleculeFactory.random_molecule([Elements.C], 2))

    organism = Organism(matter=matter, genome=genome)
    organism.position = (x, y)
    organism.energy = max_energy

    if fertile:
        while organism.reserve.mass < Organism.REPRODUCE_MATTER_THRESHOLD:
            extra = Matter()
            extra.add_molecule(MoleculeFactory.simple_organic())
            organism.digest(extra)

    return organism


def make_food():
    matter = Matter()
    matter.add_molecule(MoleculeFactory.water())
    return Substance(matter, color=(255, 255, 0))


def test_initial_spawn_counts_toward_total_organisms():
    world = World()
    assert world.total_organisms_count == len(world.organisms) == 10


def test_add_organism_increments_total_but_not_alive_only_counters():
    world = World()
    before = world.total_organisms_count

    world.add_organism(make_organism())

    assert world.total_organisms_count == before + 1
    assert world.deaths_count == 0


def test_total_organisms_survives_deaths():
    world = World()
    for organism in list(world.organisms):
        world.remove_organism(organism)

    total_before = world.total_organisms_count
    organism = make_organism()
    world.add_organism(organism)
    organism.die()

    world.update(1 / 60)

    assert world.deaths_count == 1
    assert world.total_organisms_count == total_before + 1
    assert len(world.organisms) == 0


def test_food_eaten_count_increments_on_eat_collision():
    world = World()
    for organism in list(world.organisms):
        world.remove_organism(organism)
    for substance in list(world.substances):
        world.remove_substance(substance)

    organism = make_organism()
    world.add_organism(organism)

    food = make_food()
    world.add_substance(food)

    arbiter = FakeArbiter(
        FakeShape(organism, collision_type=2),
        FakeShape(food, collision_type=1),
    )
    world.on_organism_eat_substance(arbiter, None, None)

    assert world.food_eaten_count == 1
    assert food not in world.substances


def test_reproduction_updates_births_total_and_generation_counters():
    world = World()
    for organism in list(world.organisms):
        world.remove_organism(organism)

    a = make_organism(x=0.0, y=0.0, fertile=True)
    b = make_organism(x=1.0, y=0.0, fertile=True)
    world.add_organism(a)
    world.add_organism(b)
    total_before = world.total_organisms_count

    arbiter = FakeArbiter(
        FakeShape(a, collision_type=2),
        FakeShape(b, collision_type=2),
    )
    world.on_organism_collision(arbiter, None, None)

    assert world.births_count == 1
    assert world.total_organisms_count == total_before + 1
    assert world.max_generation_reached == 1
    assert len(world.organisms) == 3
