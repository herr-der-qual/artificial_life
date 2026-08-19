import random

from core.organism_builder import OrganismBuilder
from core.molecule_factory import MoleculeFactory
from simulation.genome import Genome
from simulation.matter import Matter
from simulation.elements import Elements
from simulation.organism import Organism
from simulation.reactor import Reactor


class OrganismFactory:
    BODY_ELEMENTS = [
        Elements.H, Elements.C, Elements.N, Elements.O,
        Elements.P, Elements.S,
    ]

    @staticmethod
    def create_predator():
        pass

    @staticmethod
    def create_prey():
        pass

    @staticmethod
    def create_random():
        genome = Genome.random()

        matter = Matter()
        num_atoms = random.randint(2, 6)
        matter.add_molecule(MoleculeFactory.random_molecule(OrganismFactory.BODY_ELEMENTS, num_atoms))

        x = random.uniform(-300, 300)
        y = random.uniform(-300, 300)

        return (
            OrganismBuilder()
                .set_position((x, y))
                .set_genome(genome)
                .set_matter(matter)
                .build()
        )

    @staticmethod
    def create_basic():
        genome = Genome(speed=30, max_energy=100, energy_drain_rate=10, search_radius=200, color=(255, 255, 0))

        matter = Matter()
        matter.add_molecule(MoleculeFactory.random_molecule([Elements.C], 3))

        return (
            OrganismBuilder()
                .set_position((100, 100))
                .set_genome(genome)
                .set_matter(matter)
                .build()
        )

    @staticmethod
    def create_offspring(parent_a: Organism, parent_b: Organism):
        """Sexual reproduction: both parents pay an energy cost and hand
        over their accumulated leftover digestion products (reserve), which
        chemically react together (same Reactor used for digestion/free
        chemistry) to form the child's body. Traits are crossed over from
        both genomes and mutated."""
        if not parent_a.can_reproduce() or not parent_b.can_reproduce():
            return None

        parent_a.energy -= Organism.REPRODUCE_ENERGY_COST
        parent_b.energy -= Organism.REPRODUCE_ENERGY_COST
        parent_a.reproduction_cooldown = Organism.REPRODUCE_COOLDOWN
        parent_b.reproduction_cooldown = Organism.REPRODUCE_COOLDOWN

        reserve_molecules = parent_a.reserve.molecules + parent_b.reserve.molecules
        parent_a.reserve = Matter()
        parent_b.reserve = Matter()

        result = Reactor.react(reserve_molecules, catalyzed=True)
        matter = Matter()
        for product in result.products:
            matter.add_molecule(product)

        genome = parent_a.genome.crossover(parent_b.genome).mutate()
        starting_energy = min(
            genome.max_energy,
            Organism.REPRODUCE_ENERGY_COST + max(0.0, result.energy_delta),
        )
        generation = max(parent_a.generation, parent_b.generation) + 1

        midpoint = (
            (parent_a.position.x + parent_b.position.x) / 2,
            (parent_a.position.y + parent_b.position.y) / 2,
        )

        return (
            OrganismBuilder()
                .set_position(midpoint)
                .set_genome(genome)
                .set_matter(matter)
                .set_starting_energy(starting_energy)
                .set_generation(generation)
                .build()
        )

    @staticmethod
    def create_from_json(file_path):
        pass
