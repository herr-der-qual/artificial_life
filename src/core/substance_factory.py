import random
import pymunk

from simulation.substance import Substance
from simulation.matter import Matter
from simulation.elements import Elements
from core.molecule_factory import MoleculeFactory
from core.earth_abundance import weighted_element_pool


class SubstanceFactory:
    """Factory for creating food substances with different compositions.
    All food is shades of blue, so it reads clearly against the warmer
    organism palette (Genome.random() colors)."""

    @staticmethod
    def create_basic():
        """Create basic food substance with simple composition (CO2)"""
        matter = Matter()
        matter.add_molecule(MoleculeFactory.co2())

        return Substance(matter, color=(70, 130, 220), kind="basic")

    @staticmethod
    def create_rich():
        """Create nutrient-rich food substance (small organic molecule)"""
        matter = Matter()
        matter.add_molecule(MoleculeFactory.simple_organic())

        return Substance(matter, color=(20, 60, 160), kind="rich")

    @staticmethod
    def create_simple():
        """Create simple low-energy food (water)"""
        matter = Matter()
        matter.add_molecule(MoleculeFactory.water())

        return Substance(matter, color=(120, 190, 255), kind="simple")

    @staticmethod
    def create_mineral():
        """Rock-forming food: elements picked in real Earth-crust
        proportions (mostly O/Si/Al - see core.earth_abundance), not the
        fixed CHNOPS recipes above. Whether it's worth eating is for
        natural selection to decide (silicate-like bonds may not digest
        into much usable energy) - same as any other food kind."""
        matter = Matter()
        pool = weighted_element_pool()
        matter.add_molecule(MoleculeFactory.random_molecule(pool, random.randint(2, 4)))

        return Substance(matter, color=(150, 170, 200), kind="mineral")

    @staticmethod
    def create_random():
        """Create random food substance. Mineral (crust-like) food spawns
        more often than the organic recipes, roughly echoing how real
        rock-forming matter vastly outweighs biologically useful matter -
        without going all the way to the real ratio, which would leave
        almost no organic food to actually sustain a population."""
        types = [
            SubstanceFactory.create_mineral,
            SubstanceFactory.create_basic,
            SubstanceFactory.create_rich,
            SubstanceFactory.create_simple,
        ]
        weights = [40, 20, 20, 20]
        return random.choices(types, weights=weights, k=1)[0]()

    @staticmethod
    def spawn_at_position(substance_type='basic', x=0, y=0):
        """Create and position a substance at specific coordinates"""
        if substance_type == 'basic':
            substance = SubstanceFactory.create_basic()
        elif substance_type == 'rich':
            substance = SubstanceFactory.create_rich()
        elif substance_type == 'simple':
            substance = SubstanceFactory.create_simple()
        elif substance_type == 'mineral':
            substance = SubstanceFactory.create_mineral()
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
        Elements.C: (40, 90, 190),
        Elements.O: (90, 150, 230),
        Elements.H: (140, 200, 255),
        Elements.N: (60, 110, 210),
        Elements.S: (30, 70, 170),
        Elements.P: (100, 170, 240),
        # Crust/mineral elements (see core.earth_abundance) - grayer,
        # cooler blues to read as "rock" rather than "organic".
        Elements.Si: (130, 150, 175),
        Elements.Al: (150, 165, 185),
        Elements.Na: (115, 140, 170),
        Elements.Mg: (100, 130, 165),
        Elements.Cl: (80, 160, 200),
        Elements.F: (170, 190, 210),
        Elements.Li: (120, 145, 175),
        Elements.B: (110, 135, 165),
    }

    @staticmethod
    def color_for(matter: Matter):
        """Derive a display color from a matter's dominant element - used for
        substances produced by a reaction rather than a fixed recipe. Still
        blue-family, to read as food."""
        if not matter.molecules:
            return (100, 150, 220)

        counts = {}
        for molecule in matter.molecules:
            for element, count in molecule.formula().items():
                counts[element] = counts.get(element, 0) + count

        dominant = max(counts.items(), key=lambda kv: kv[1])[0]
        return SubstanceFactory.ELEMENT_COLORS.get(dominant, (100, 150, 220))
