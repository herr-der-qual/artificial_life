import random
import pymunk

from simulation.substance import Substance
from simulation.matter import Matter
from simulation.elements import Elements
from core.molecule_factory import MoleculeFactory


class SubstanceFactory:
    """Factory for creating food substances with different compositions"""

    @staticmethod
    def create_basic():
        """Create basic food substance with simple composition (CO2)"""
        matter = Matter()
        matter.add_molecule(MoleculeFactory.co2())

        substance = Substance(matter, color=(255, 200, 0))
        return substance

    @staticmethod
    def create_rich():
        """Create nutrient-rich food substance (small organic molecule)"""
        matter = Matter()
        matter.add_molecule(MoleculeFactory.simple_organic())

        substance = Substance(matter, color=(255, 150, 0))
        return substance

    @staticmethod
    def create_simple():
        """Create simple low-energy food (water)"""
        matter = Matter()
        matter.add_molecule(MoleculeFactory.water())

        substance = Substance(matter, color=(255, 255, 0))
        return substance

    @staticmethod
    def create_random():
        """Create random food substance"""
        types = [
            SubstanceFactory.create_basic,
            SubstanceFactory.create_rich,
            SubstanceFactory.create_simple
        ]
        return random.choice(types)()

    @staticmethod
    def spawn_at_position(substance_type='basic', x=0, y=0):
        """Create and position a substance at specific coordinates"""
        if substance_type == 'basic':
            substance = SubstanceFactory.create_basic()
        elif substance_type == 'rich':
            substance = SubstanceFactory.create_rich()
        elif substance_type == 'simple':
            substance = SubstanceFactory.create_simple()
        elif substance_type == 'random':
            substance = SubstanceFactory.create_random()
        else:
            substance = SubstanceFactory.create_basic()

        substance.position = (x, y)
        return substance

    @staticmethod
    def spawn_random_in_bounds(min_x=-400, max_x=400, min_y=-400, max_y=400, substance_type='random'):
        """Spawn substance at random position within bounds"""
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)
        return SubstanceFactory.spawn_at_position(substance_type, x, y)

    ELEMENT_COLORS = {
        Elements.C: (180, 120, 60),
        Elements.O: (255, 100, 100),
        Elements.H: (200, 200, 255),
        Elements.N: (150, 150, 255),
        Elements.S: (230, 230, 0),
        Elements.P: (255, 150, 200),
    }

    @staticmethod
    def color_for(matter: Matter):
        """Derive a display color from a matter's dominant element - used for
        substances produced by a reaction rather than a fixed recipe."""
        if not matter.molecules:
            return (200, 200, 200)

        counts = {}
        for molecule in matter.molecules:
            for element, count in molecule.formula().items():
                counts[element] = counts.get(element, 0) + count

        dominant = max(counts.items(), key=lambda kv: kv[1])[0]
        return SubstanceFactory.ELEMENT_COLORS.get(dominant, (200, 200, 200))
