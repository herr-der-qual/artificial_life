import random
from dataclasses import dataclass

# Same baseline as the pymunk system's Genome (simulation.genome) - kept
# separate rather than shared, since this genome's actual fields are much
# smaller (no diet/cell_count/search_radius: this world has neither
# predation nor a brain to use a search radius with yet).
BASE_MUTATION_RATE = 0.15


def _jitter(value: float, rate: float) -> float:
    return max(0.01, value * random.uniform(1 - rate, 1 + rate))


def _jitter_channel(value: int, rate: float) -> int:
    delta = int(value * rate)
    return max(0, min(255, value + random.randint(-delta, delta) if delta else value))


@dataclass
class Genome:
    """Heritable traits for a grid Organism: what a new organism starts
    with, independent of the actual matter its body is built from -
    deliberately smaller than the pymunk system's Genome for now, just
    enough that reproduction (see OrganismFactory.create_offspring_asexual)
    produces real, visible variation instead of identical clones."""

    max_energy: float
    energy_drain_rate: float
    color: tuple

    def mutate(self, rate: float = BASE_MUTATION_RATE) -> 'Genome':
        return Genome(
            max_energy=_jitter(self.max_energy, rate),
            energy_drain_rate=_jitter(self.energy_drain_rate, rate),
            color=tuple(_jitter_channel(c, rate) for c in self.color),
        )

    @staticmethod
    def random() -> 'Genome':
        return Genome(
            max_energy=random.uniform(70, 130),
            energy_drain_rate=random.uniform(1.5, 3.0),
            color=(
                random.randint(150, 255),
                random.randint(200, 255),
                random.randint(0, 100),
            ),
        )
