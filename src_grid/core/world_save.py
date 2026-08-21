import json
from pathlib import Path

from simulation.elements import Elements
from simulation.matter import Matter
from simulation.molecule import Molecule

from src_grid.core.world_config import WorldConfig
from src_grid.simulation.food import Food
from src_grid.simulation.organism import Organism
from src_grid.simulation.world import World

WORLD_SAVE_PATH = Path(__file__).resolve().parent.parent.parent / "grid_world_save.json"
GRID_SAVES_DIR = Path(__file__).resolve().parent.parent.parent / "grid_saves"


def _serialize_matter(matter: Matter) -> dict:
    molecules = []
    for molecule in matter.molecules:
        atom_index = {id(atom): i for i, atom in enumerate(molecule.atoms)}
        molecules.append({
            "atoms": [atom.element.name for atom in molecule.atoms],
            "bonds": [
                [atom_index[id(bond.atom_a)], atom_index[id(bond.atom_b)], bond.order]
                for bond in molecule.bonds
            ],
        })
    return {"molecules": molecules}


def _deserialize_matter(data: dict) -> Matter:
    matter = Matter()
    for molecule_data in data["molecules"]:
        molecule = Molecule()
        atoms = [molecule.add_atom(Elements[name]) for name in molecule_data["atoms"]]
        for atom_a_index, atom_b_index, order in molecule_data["bonds"]:
            molecule.add_bond(atoms[atom_a_index], atoms[atom_b_index], order)
        matter.add_molecule(molecule)
    return matter


def world_to_dict(world: World) -> dict:
    """The full live state - every food/organism's exact position and real
    chemistry, not just the recipe that could have produced *a* world like
    it (see WorldConfig for that). Resuming from this should look
    identical to however the world looked the moment it was saved."""
    organism_ids = {id(organism) for organism in world.organisms}

    food_entries = []
    organism_entries = []
    for entity in world.grid:
        col, row = entity.position
        entry = {
            "col": col,
            "row": row,
            "color": list(entity.color),
            "matter": _serialize_matter(entity.matter),
        }
        if id(entity) in organism_ids:
            entry["energy"] = entity.energy
            entry["generation"] = entity.generation
            entry["reproduction_cooldown"] = entity.reproduction_cooldown
            entry["reserve"] = _serialize_matter(entity.reserve)
            organism_entries.append(entry)
        else:
            entry["kind"] = entity.kind
            food_entries.append(entry)

    return {
        "tick_count": world.tick_count,
        "deaths_count": world.deaths_count,
        "food_eaten_count": world.food_eaten_count,
        "births_count": world.births_count,
        "max_generation_reached": world.max_generation_reached,
        "grid": {"width": world.grid.width, "height": world.grid.height},
        "food": food_entries,
        "organisms": organism_entries,
    }


def world_from_dict(data: dict) -> World:
    config = WorldConfig()
    config.data["width"] = data["grid"]["width"]
    config.data["height"] = data["grid"]["height"]
    # The save already carries every entity's exact state - spawning fresh
    # ones on top would be a bug, not a feature.
    config.data["food_count"] = 0
    config.data["organism_count"] = 0

    world = World(config)
    world.tick_count = data["tick_count"]
    world.deaths_count = data.get("deaths_count", 0)
    world.food_eaten_count = data.get("food_eaten_count", 0)
    world.births_count = data.get("births_count", 0)
    world.max_generation_reached = data.get("max_generation_reached", 0)

    for entry in data["food"]:
        food = Food(_deserialize_matter(entry["matter"]), tuple(entry["color"]), entry["kind"])
        world.grid.place(food, entry["col"], entry["row"])

    for entry in data["organisms"]:
        organism = Organism(
            _deserialize_matter(entry["matter"]), tuple(entry["color"]),
            energy=entry.get("energy"), generation=entry.get("generation", 0),
        )
        organism.reproduction_cooldown = entry.get("reproduction_cooldown", 0)
        if "reserve" in entry:
            organism.reserve = _deserialize_matter(entry["reserve"])
        world.grid.place(organism, entry["col"], entry["row"])
        world.organisms.append(organism)

    return world


def save_world(world: World, path: Path = WORLD_SAVE_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(world_to_dict(world), f, indent=2)


def load_world(path: Path = WORLD_SAVE_PATH) -> World:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return world_from_dict(data)
