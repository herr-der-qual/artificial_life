import random
import pymunk

from simulation.substance import Substance
from simulation.matter import Matter
from simulation.elements import Elements


class SubstanceFactory:
    """Factory for creating food substances with different compositions"""

    @staticmethod
    def create_basic():
        """Create basic food substance with simple composition"""
        matter = Matter()
        matter.add_elements([Elements.C, Elements.O])

        substance = Substance(matter, color=(255, 200, 0))
        return substance

    @staticmethod
    def create_rich():
        """Create nutrient-rich food substance"""
        matter = Matter()
        matter.add_elements([Elements.C, Elements.C, Elements.O, Elements.N])

        substance = Substance(matter, color=(255, 150, 0))
        return substance

    @staticmethod
    def create_simple():
        """Create simple low-energy food"""
        matter = Matter()
        matter.add_elements([Elements.H, Elements.O])

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
