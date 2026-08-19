from core.molecule_factory import MoleculeFactory
from core.world_config import WorldConfig
from simulation.elements import Elements
from simulation.genome import Genome
from simulation.matter import Matter
from simulation.organism import Organism
from simulation.substance import Substance, FOOD_KINDS
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
                     search_radius=200.0, wander_radius=50.0, diet=frozenset(FOOD_KINDS),
                     color=(0, 255, 0))
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
    return Substance(matter, color=(255, 255, 0), kind="simple")


def make_reactive_substance(x=0.0, y=0.0, kind="reaction_product"):
    """A lone, fully-unsaturated atom - guaranteed free valence so two of
    these actually react (needed to exercise the bond-breaking path)."""
    matter = Matter()
    matter.add_molecule(MoleculeFactory.random_molecule([Elements.C], 1))
    substance = Substance(matter, color=(0, 0, 255), kind=kind)
    substance.position = (x, y)
    return substance


def test_initial_spawn_counts_toward_total_organisms(tmp_path):
    world = World(WorldConfig(path=tmp_path / "world_config.json"))
    assert world.total_organisms_count == len(world.organisms) == 10


def test_world_respects_custom_config(tmp_path):
    config = WorldConfig(path=tmp_path / "world_config.json")
    config.data["initial_organism_count"] = 3
    config.data["initial_substance_count"] = 7
    config.data["organism_spawn_bound"] = 50.0
    config.data["substance_spawn_bound"] = 60.0

    world = World(config)

    assert len(world.organisms) == 3
    assert len(world.substances) == 7
    assert all(abs(o.position.x) <= 50.0 and abs(o.position.y) <= 50.0 for o in world.organisms)
    assert all(abs(s.position.x) <= 60.0 and abs(s.position.y) <= 60.0 for s in world.substances)


def test_initial_organisms_spawn_without_overlapping(tmp_path):
    config = WorldConfig(path=tmp_path / "world_config.json")
    config.data["initial_organism_count"] = 60
    config.data["initial_substance_count"] = 0
    config.data["organism_spawn_bound"] = 300.0

    world = World(config)
    positions = [o.position for o in world.organisms]

    # organisms are ~8 units across - grid spawning should keep every pair
    # farther apart than that, unlike independent random placement which
    # can stack several right on top of each other.
    min_distance = min(
        (positions[i] - positions[j]).length
        for i in range(len(positions))
        for j in range(i + 1, len(positions))
    )
    assert min_distance > 8.0


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


def test_eat_collision_is_ignored_when_food_kind_is_outside_diet():
    world = World()
    for organism in list(world.organisms):
        world.remove_organism(organism)
    for substance in list(world.substances):
        world.remove_substance(substance)

    organism = make_organism()
    organism.diet = frozenset({"rich"})  # water ("simple") is not in the diet
    world.add_organism(organism)

    food = make_food()
    world.add_substance(food)

    arbiter = FakeArbiter(
        FakeShape(organism, collision_type=2),
        FakeShape(food, collision_type=1),
    )
    world.on_organism_eat_substance(arbiter, None, None)

    assert world.food_eaten_count == 0
    assert food in world.substances


def test_eating_the_same_substance_twice_in_one_step_does_not_crash():
    """At high entity density, pymunk can fire the eat-collision `begin`
    callback for the same substance twice within a single physics step
    (e.g. two organisms touching it before removal takes effect). The
    second pass used to re-run Reactor.react on already-mutated bonds and
    raise ValueError: list.remove(x): x not in list."""
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
    world.on_organism_eat_substance(arbiter, None, None)  # must not raise

    assert world.food_eaten_count == 1


def test_substance_collision_ignores_an_already_removed_substance():
    """Same double-processing hazard as eating, but for the free-chemistry
    substance-substance collision handler."""
    world = World()
    for substance in list(world.substances):
        world.remove_substance(substance)

    a = make_reactive_substance(0.0, 0.0)
    b = make_reactive_substance(1.0, 0.0)
    c = make_reactive_substance(2.0, 0.0)
    world.add_substance(a)
    world.add_substance(b)
    world.add_substance(c)

    first_arbiter = FakeArbiter(FakeShape(a, collision_type=1), FakeShape(b, collision_type=1))
    world.on_substance_collision(first_arbiter, None, None)
    assert a.removed and b.removed

    # a is already gone - a second, overlapping callback pairing it with c
    # must be a safe no-op, not a crash.
    second_arbiter = FakeArbiter(FakeShape(a, collision_type=1), FakeShape(c, collision_type=1))
    world.on_substance_collision(second_arbiter, None, None)  # must not raise

    assert c in world.substances
    assert c.matter.mass > 0


def test_food_spawns_over_time(tmp_path):
    config = WorldConfig(path=tmp_path / "world_config.json")
    config.data["initial_organism_count"] = 0
    config.data["initial_substance_count"] = 0
    config.data["food_spawn_interval"] = 1.0
    config.data["food_spawn_count"] = 4

    world = World(config)
    assert len(world.substances) == 0

    world.update(0.5)
    assert len(world.substances) == 0  # interval hasn't elapsed yet

    world.update(0.6)
    assert len(world.substances) == 4


def test_food_spawn_respects_max_substance_count(tmp_path):
    config = WorldConfig(path=tmp_path / "world_config.json")
    config.data["initial_organism_count"] = 0
    config.data["initial_substance_count"] = 0
    config.data["food_spawn_interval"] = 1.0
    config.data["food_spawn_count"] = 10
    config.data["max_substance_count"] = 3

    world = World(config)
    world.update(1.5)

    assert len(world.substances) == 3


def test_food_spawn_disabled_when_interval_is_zero(tmp_path):
    config = WorldConfig(path=tmp_path / "world_config.json")
    config.data["initial_organism_count"] = 0
    config.data["initial_substance_count"] = 0
    config.data["food_spawn_interval"] = 0

    world = World(config)
    world.update(100.0)

    assert len(world.substances) == 0


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
