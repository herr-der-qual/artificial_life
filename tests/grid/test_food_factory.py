from core.earth_abundance import CRUST_ABUNDANCE_PERCENT
from src_grid.core.food_factory import FoodFactory
from src_grid.simulation.food import Food


def test_create_random_produces_food():
    food = FoodFactory.create_random()
    assert isinstance(food, Food)
    assert food.matter.mass > 0


def test_create_mineral_only_uses_crust_elements():
    food = FoodFactory.create_mineral()
    molecule = food.matter.molecules[0]
    for atom in molecule.atoms:
        assert atom.element in CRUST_ABUNDANCE_PERCENT


def test_create_random_spawns_mineral_food_most_often():
    counts = {"basic": 0, "rich": 0, "simple": 0, "mineral": 0}
    for _ in range(500):
        food = FoodFactory.create_random()
        counts[food.kind] += 1

    assert counts["mineral"] > counts["basic"]
    assert counts["mineral"] > counts["rich"]
    assert counts["mineral"] > counts["simple"]
    assert all(count > 0 for count in counts.values())
