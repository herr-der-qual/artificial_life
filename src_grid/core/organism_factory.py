import random

from core.molecule_factory import MoleculeFactory
from core.organism_factory import OrganismFactory as PymunkOrganismFactory
from simulation.matter import Matter
from simulation.reactor import Reactor

from src_grid.simulation.organism import Organism

# How far a channel can drift on reproduction - keeps color a real,
# visible heritable trait (see create_offspring_asexual) without the full
# Genome dataclass this system doesn't have yet.
COLOR_MUTATION_RATE = 0.15


def _mutate_color(color: tuple) -> tuple:
    def jitter(channel: int) -> int:
        delta = int(channel * COLOR_MUTATION_RATE)
        return max(0, min(255, channel + random.randint(-delta, delta) if delta else channel))

    return tuple(jitter(c) for c in color)


class OrganismFactory:
    """Reuses the same body-building recipe (CHNOPS elements, 2-6 atoms) as
    the pymunk-based OrganismFactory, without any of its pymunk/genome
    machinery - this system doesn't have full genetics yet, just a
    mutating color so reproduction has something heritable to show for
    itself on screen."""

    @staticmethod
    def create_random() -> Organism:
        matter = Matter()
        num_atoms = random.randint(2, 6)
        matter.add_molecule(MoleculeFactory.random_molecule(PymunkOrganismFactory.BODY_ELEMENTS, num_atoms))
        return Organism(matter, color=(220, 220, 80))

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

        starting_energy = min(
            Organism.MAX_ENERGY,
            Organism.MAX_ENERGY * 0.6 + max(0.0, result.energy_delta),
        )

        return Organism(
            matter, _mutate_color(parent.color),
            energy=starting_energy, generation=parent.generation + 1,
        )
