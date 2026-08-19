from ai.tasks.seek_food_task import SeekFoodTask
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


def make_food(x, y, kind="basic"):
    matter = Matter()
    matter.add_molecule(MoleculeFactory.water())
    substance = Substance(matter, color=(0, 0, 255), kind=kind)
    substance.position = (x, y)
    return substance


def make_organism(search_radius=200.0, diet=frozenset(FOOD_KINDS)):
    genome = Genome(speed=30.0, max_energy=100.0, energy_drain_rate=10.0,
                     search_radius=search_radius, wander_radius=50.0, diet=diet,
                     color=(0, 255, 0))
    matter = Matter()
    matter.add_molecule(MoleculeFactory.random_molecule([Elements.C], 2))
    return Organism(matter=matter, genome=genome)


def test_ignores_food_outside_its_own_search_radius(tmp_path):
    world = make_empty_world(tmp_path)
    organism = make_organism(search_radius=50.0)
    world.add_substance(make_food(100.0, 0.0))

    task = SeekFoodTask(organism, world)
    assert task.find_nearest_food() is None


def test_finds_food_within_its_own_search_radius(tmp_path):
    world = make_empty_world(tmp_path)
    organism = make_organism(search_radius=150.0)
    food = make_food(100.0, 0.0)
    world.add_substance(food)

    task = SeekFoodTask(organism, world)
    assert task.find_nearest_food() is food


def test_wider_genome_search_radius_sees_further(tmp_path):
    world = make_empty_world(tmp_path)
    narrow = make_organism(search_radius=50.0)
    wide = make_organism(search_radius=150.0)
    food = make_food(100.0, 0.0)
    world.add_substance(food)

    assert SeekFoodTask(narrow, world).find_nearest_food() is None
    assert SeekFoodTask(wide, world).find_nearest_food() is food


def test_ignores_food_kinds_outside_its_diet(tmp_path):
    world = make_empty_world(tmp_path)
    organism = make_organism(diet=frozenset({"rich", "simple"}))
    world.add_substance(make_food(10.0, 0.0, kind="basic"))

    assert SeekFoodTask(organism, world).find_nearest_food() is None


def test_targets_food_kinds_within_its_diet(tmp_path):
    world = make_empty_world(tmp_path)
    organism = make_organism(diet=frozenset({"basic"}))
    food = make_food(10.0, 0.0, kind="basic")
    world.add_substance(food)

    assert SeekFoodTask(organism, world).find_nearest_food() is food


def test_skips_disliked_food_in_favor_of_a_farther_accepted_one(tmp_path):
    world = make_empty_world(tmp_path)
    organism = make_organism(diet=frozenset({"simple"}))
    world.add_substance(make_food(5.0, 0.0, kind="basic"))
    accepted_but_farther = make_food(40.0, 0.0, kind="simple")
    world.add_substance(accepted_but_farther)

    assert SeekFoodTask(organism, world).find_nearest_food() is accepted_but_farther


def test_do_retargets_once_the_current_target_is_removed(tmp_path):
    world = make_empty_world(tmp_path)
    organism = make_organism(search_radius=150.0)
    organism.position = (0.0, 0.0)
    near_food = make_food(20.0, 0.0)
    far_food = make_food(100.0, 0.0)
    world.add_substance(near_food)
    world.add_substance(far_food)

    task = SeekFoodTask(organism, world)
    task.do()
    assert task.target_food is near_food

    world.remove_substance(near_food)
    task.do()
    assert task.target_food is far_food
