from core.earth_abundance import CRUST_ABUNDANCE_PERCENT
from core.substance_factory import SubstanceFactory


def test_create_mineral_produces_a_valid_food_substance():
    substance = SubstanceFactory.create_mineral()
    assert substance.kind == "mineral"
    assert substance.matter.mass > 0


def test_create_mineral_only_uses_crust_elements():
    substance = SubstanceFactory.create_mineral()
    molecule = substance.matter.molecules[0]
    for atom in molecule.atoms:
        assert atom.element in CRUST_ABUNDANCE_PERCENT


def test_create_random_spawns_mineral_food_most_often():
    """Mineral (crust-like) food is weighted heaviest in create_random -
    see SubstanceFactory.create_random for the reasoning."""
    counts = {"basic": 0, "rich": 0, "simple": 0, "mineral": 0}
    for _ in range(500):
        substance = SubstanceFactory.create_random()
        counts[substance.kind] += 1

    assert counts["mineral"] > counts["basic"]
    assert counts["mineral"] > counts["rich"]
    assert counts["mineral"] > counts["simple"]
    assert all(count > 0 for count in counts.values())


def test_spawn_at_position_supports_mineral_type():
    substance = SubstanceFactory.spawn_at_position("mineral", x=10.0, y=20.0)
    assert substance.kind == "mineral"
    assert substance.position.x == 10.0
    assert substance.position.y == 20.0
