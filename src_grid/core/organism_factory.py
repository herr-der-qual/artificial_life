import random

from core.molecule_factory import MoleculeFactory
from core.organism_factory import OrganismFactory as PymunkOrganismFactory
from simulation.matter import Matter

from src_grid.simulation.organism import Organism


class OrganismFactory:
    """Reuses the same body-building recipe (CHNOPS elements, 2-6 atoms) as
    the pymunk-based OrganismFactory, without any of its pymunk/genome
    machinery - this system doesn't have genetics yet."""

    @staticmethod
    def create_random() -> Organism:
        matter = Matter()
        num_atoms = random.randint(2, 6)
        matter.add_molecule(MoleculeFactory.random_molecule(PymunkOrganismFactory.BODY_ELEMENTS, num_atoms))
        return Organism(matter, color=(220, 220, 80))
