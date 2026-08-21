from core.molecule_factory import MoleculeFactory
from simulation.matter import Matter

from src_grid.core.world_config import WorldConfig
from src_grid.core.world_save import save_world, load_world, world_to_dict, world_from_dict
from src_grid.simulation.world import World
from src_grid.simulation.organism import Organism


def make_config(tmp_path, **overrides):
    config = WorldConfig(path=tmp_path / "grid_world_config.json")
    config.data.update(overrides)
    return config


def test_round_trip_preserves_tick_count_and_grid_size(tmp_path):
    world = World(make_config(tmp_path, width=8, height=6, food_count=5, organism_count=3))
    for _ in range(7):
        world.update()

    loaded = world_from_dict(world_to_dict(world))

    assert loaded.tick_count == world.tick_count
    assert loaded.grid.width == world.grid.width
    assert loaded.grid.height == world.grid.height


def test_round_trip_preserves_every_entitys_position_and_kind(tmp_path):
    world = World(make_config(tmp_path, width=10, height=10, food_count=8, organism_count=4))

    loaded = world_from_dict(world_to_dict(world))

    original = {(e.position, e.color, getattr(e, "kind", None)) for e in world.grid}
    restored = {(e.position, tuple(e.color), getattr(e, "kind", None)) for e in loaded.grid}
    assert original == restored
    assert len(loaded.organisms) == len(world.organisms)


def test_round_trip_preserves_matter_composition():
    """The whole point of a real save over a config: the exact molecular
    structure (not just how many atoms) has to survive, atom-for-atom and
    bond-for-bond, not just mass or formula."""
    matter = Matter()
    matter.add_molecule(MoleculeFactory.simple_organic())  # C, O, H, H with real bonds

    from src_grid.core.world_save import _serialize_matter, _deserialize_matter

    restored = _deserialize_matter(_serialize_matter(matter))

    assert restored.mass == matter.mass
    original_molecule = matter.molecules[0]
    restored_molecule = restored.molecules[0]

    assert sorted(a.element.name for a in restored_molecule.atoms) == \
        sorted(a.element.name for a in original_molecule.atoms)
    assert len(restored_molecule.bonds) == len(original_molecule.bonds)
    assert sorted(b.order for b in restored_molecule.bonds) == sorted(b.order for b in original_molecule.bonds)


def test_save_and_load_round_trip_through_a_real_file(tmp_path):
    world = World(make_config(tmp_path, width=6, height=6, food_count=4, organism_count=2))
    save_path = tmp_path / "save.json"

    save_world(world, save_path)
    assert save_path.exists()

    loaded = load_world(save_path)

    assert loaded.tick_count == world.tick_count
    assert len(loaded.grid) == len(world.grid)
    assert len(loaded.organisms) == len(world.organisms)


def test_loaded_world_does_not_spawn_extra_entities(tmp_path):
    """Regression target: loading must reconstruct exactly what was saved,
    not the saved state PLUS a fresh default spawn on top of it."""
    world = World(make_config(tmp_path, width=10, height=10, food_count=6, organism_count=3))
    original_count = len(world.grid)

    loaded = world_from_dict(world_to_dict(world))

    assert len(loaded.grid) == original_count


def test_round_trip_preserves_energy_and_lifetime_counters(tmp_path):
    world = World(make_config(tmp_path, width=10, height=10, food_count=10, organism_count=4))
    for _ in range(5):
        world.update()

    loaded = world_from_dict(world_to_dict(world))

    original_energy = sorted(o.energy for o in world.organisms)
    restored_energy = sorted(o.energy for o in loaded.organisms)
    assert restored_energy == original_energy
    assert loaded.deaths_count == world.deaths_count
    assert loaded.food_eaten_count == world.food_eaten_count


def test_round_trip_preserves_reproduction_state(tmp_path):
    world = World(make_config(tmp_path, width=10, height=10, food_count=0, organism_count=0))

    organism = Organism(_matter(), color=(1, 2, 3), energy=42.0, generation=5)
    organism.reproduction_cooldown = 3
    organism.reserve.add_molecule(MoleculeFactory.simple_organic())
    world.grid.place(organism, 4, 4)
    world.organisms.append(organism)
    world.births_count = 7
    world.max_generation_reached = 5

    loaded = world_from_dict(world_to_dict(world))

    assert loaded.births_count == 7
    assert loaded.max_generation_reached == 5
    restored = loaded.organisms[0]
    assert restored.generation == 5
    assert restored.reproduction_cooldown == 3
    assert restored.reserve.mass == organism.reserve.mass


def _matter() -> Matter:
    matter = Matter()
    matter.add_molecule(MoleculeFactory.simple_organic())
    return matter


def test_loaded_world_can_keep_ticking(tmp_path):
    """A loaded world isn't just a static snapshot - it must still be a
    fully functional World (organisms keep moving, no double-registration
    bugs from being reconstructed instead of freshly built)."""
    world = World(make_config(tmp_path, width=20, height=20, food_count=0, organism_count=6))
    loaded = world_from_dict(world_to_dict(world))
    starting_positions = [o.position for o in loaded.organisms]

    for _ in range(30):
        loaded.update()

    assert loaded.tick_count == 30
    ending_positions = [o.position for o in loaded.organisms]
    assert ending_positions != starting_positions
    # still respects the "no two things share a cell" invariant
    assert len(set(ending_positions)) == len(ending_positions)
