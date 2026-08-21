import random

from core.earth_abundance import weighted_element_pool
from core.molecule_factory import MoleculeFactory
from simulation.matter import Matter

from src_grid.simulation.food import Food


class FoodFactory:
    """Mirrors SubstanceFactory's recipes (same chemistry, same colors) but
    builds a Food instead of a pymunk-backed Substance - kept separate
    rather than shared, since the grid rewrite is deliberately decoupled
    from the pymunk world while it's being explored."""

    @staticmethod
    def create_basic() -> Food:
        matter = Matter()
        matter.add_molecule(MoleculeFactory.co2())
        return Food(matter, color=(70, 130, 220), kind="basic")

    @staticmethod
    def create_rich() -> Food:
        matter = Matter()
        matter.add_molecule(MoleculeFactory.simple_organic())
        return Food(matter, color=(20, 60, 160), kind="rich")

    @staticmethod
    def create_simple() -> Food:
        matter = Matter()
        matter.add_molecule(MoleculeFactory.water())
        return Food(matter, color=(120, 190, 255), kind="simple")

    @staticmethod
    def create_mineral() -> Food:
        """Crust-abundance-weighted elements (see core.earth_abundance) -
        mostly O/Si/Al, real rock-forming elements, rather than the fixed
        CHNOPS recipes above."""
        matter = Matter()
        pool = weighted_element_pool()
        matter.add_molecule(MoleculeFactory.random_molecule(pool, random.randint(2, 4)))
        return Food(matter, color=(150, 170, 200), kind="mineral")

    @staticmethod
    def create_random() -> Food:
        """Mineral food spawns more often than the organic recipes -
        roughly echoing how real rock-forming matter vastly outweighs
        biologically useful matter, without going all the way to the real
        ratio (see SubstanceFactory.create_random for the same reasoning)."""
        types = [
            FoodFactory.create_mineral,
            FoodFactory.create_basic,
            FoodFactory.create_rich,
            FoodFactory.create_simple,
        ]
        weights = [40, 20, 20, 20]
        return random.choices(types, weights=weights, k=1)[0]()
