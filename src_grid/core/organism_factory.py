import random

from core.molecule_factory import MoleculeFactory
from core.organism_factory import OrganismFactory as PymunkOrganismFactory
from simulation.matter import Matter
from simulation.reactor import Reactor

from src_grid.simulation.genome import Genome
from src_grid.simulation.organism import Organism


class OrganismFactory:
    """Reuses the same body-building recipe (CHNOPS elements, 2-6 atoms) as
    the pymunk-based OrganismFactory, without any of its pymunk machinery -
    genetics comes from this system's own, smaller Genome (see
    simulation.genome) instead of the pymunk one."""

    @staticmethod
    def create_random() -> Organism:
        matter = Matter()
        num_atoms = random.randint(2, 6)
        matter.add_molecule(MoleculeFactory.random_molecule(PymunkOrganismFactory.BODY_ELEMENTS, num_atoms))
        return Organism(matter, Genome.random())

    @staticmethod
    def create_offspring_asexual(parent: Organism):
        """Solo budding: the parent alone pays the reproductive cost and
        hands its entire reserve over to build the child's body (the same
        catalyzed Reactor reaction digestion uses) - no mate required, so
        this is the only reproduction path this system has for now (see
        the pymunk OrganismFactory for the sexual-reproduction sibling of
        this, not ported here yet)."""
        if not parent.can_reproduce():
            return None

        parent.energy -= Organism.REPRODUCE_ENERGY_COST
        parent.reproduction_cooldown = Organism.REPRODUCE_COOLDOWN

        reserve_molecules = parent.reserve.molecules
        parent.reserve = Matter()

        result = Reactor.react(reserve_molecules, catalyzed=True)
        matter = Matter()
        for product in result.products:
            matter.add_molecule(product)

        genome = parent.genome.mutate()
        starting_energy = min(
            genome.max_energy,
            genome.max_energy * 0.6 + max(0.0, result.energy_delta),
        )

        return Organism(matter, genome, energy=starting_energy, generation=parent.generation + 1)
