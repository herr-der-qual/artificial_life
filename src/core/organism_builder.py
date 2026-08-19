from simulation.organism import Organism
from simulation.genome import Genome
from simulation.matter import Matter


class OrganismBuilder:
    def __init__(self):
        self.position = (0, 0)
        self.genome = None
        self.matter = None
        self.starting_energy = None

    def set_position(self, position):
        self.position = position
        return self

    def set_genome(self, genome: Genome):
        self.genome = genome
        return self

    def set_matter(self, matter: Matter):
        self.matter = matter
        return self

    def set_starting_energy(self, energy: float):
        self.starting_energy = energy
        return self

    def build(self) -> 'Organism':
        organism = Organism(
            matter=self.matter,
            genome=self.genome,
            starting_energy=self.starting_energy,
        )
        organism.position = self.position

        return organism
