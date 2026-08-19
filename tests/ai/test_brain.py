from ai.tasks.seek_food_task import SeekFoodTask
from ai.tasks.seek_mate_task import SeekMateTask
from ai.tasks.waypoint_task import WaypointTask
from core.molecule_factory import MoleculeFactory
from core.world_config import WorldConfig
from simulation.elements import Elements
from simulation.genome import Genome
from simulation.matter import Matter
from simulation.organism import Organism
from simulation.substance import Substance, FOOD_KINDS
from simulation.world import World


def make_empty_world(tmp_path):
    config = WorldConfig(path=tmp_path / "world_config.json")
    config.data["initial_organism_count"] = 0
    config.data["initial_substance_count"] = 0
    config.data["food_spawn_interval"] = 0
    return World(config)


def make_food(x=50.0, y=50.0, kind="basic"):
    matter = Matter()
    matter.add_molecule(MoleculeFactory.water())
    substance = Substance(matter, color=(0, 0, 255), kind=kind)
    substance.position = (x, y)
    return substance


def make_organism(energy_ratio=1.0, fertile=False, max_energy=200.0):
    genome = Genome(
        speed=30.0, max_energy=max_energy, energy_drain_rate=10.0, search_radius=200.0,
        wander_radius=50.0, cell_count=1, diet=frozenset(FOOD_KINDS), color=(0, 255, 0),
    )
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


def test_hunger_takes_priority_over_mating(tmp_path):
    world = make_empty_world(tmp_path)
    organism = make_organism(energy_ratio=0.1, fertile=True)
    world.add_organism(organism)
    world.add_substance(make_food())

    organism.brain.update()

    assert isinstance(organism.brain.tasks[0], SeekFoodTask)


def test_mating_pursued_when_not_hungry(tmp_path):
    world = make_empty_world(tmp_path)
    organism = make_organism(energy_ratio=1.0, fertile=True)
    mate = make_organism(energy_ratio=1.0, fertile=True)
    mate.position = (50.0, 50.0)
    world.add_organism(organism)
    world.add_organism(mate)
    world.add_substance(make_food())

    organism.brain.update()

    assert isinstance(organism.brain.tasks[0], SeekMateTask)


def test_wanders_when_no_goal_is_active(tmp_path):
    world = make_empty_world(tmp_path)
    organism = make_organism(energy_ratio=1.0, fertile=False)
    world.add_organism(organism)

    organism.brain.update()

    assert isinstance(organism.brain.tasks[0], WaypointTask)


def test_does_not_restart_the_same_goal_task_every_tick(tmp_path):
    world = make_empty_world(tmp_path)
    organism = make_organism(energy_ratio=0.1, fertile=False)
    world.add_organism(organism)
    world.add_substance(make_food())

    organism.brain.update()
    first_task = organism.brain.tasks[0]

    organism.brain.update()
    assert organism.brain.tasks[0] is first_task


def test_wander_target_is_clamped_inside_the_world_bound(tmp_path):
    """Regression target: near an edge, an unclamped wander target could
    aim further out, immediately get clipped back by World's hard bound
    clamp, and repeat every tick - grinding uselessly against the wall
    instead of actually wandering."""
    world = make_empty_world(tmp_path)
    organism = make_organism(energy_ratio=1.0, fertile=False)
    organism.wander_radius = 500.0
    organism.position = (world.world_bound - 10.0, 0.0)
    world.add_organism(organism)

    for _ in range(50):
        organism.brain.tasks.clear()
        organism.brain.update()
        task = organism.brain.tasks[0]
        assert isinstance(task, WaypointTask)
        assert -world.world_bound <= task.waypoint[0] <= world.world_bound
        assert -world.world_bound <= task.waypoint[1] <= world.world_bound
