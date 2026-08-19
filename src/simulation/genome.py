import random
from dataclasses import dataclass

from simulation.substance import FOOD_KINDS

# Chance any given food kind starts in a fresh random genome's diet - high
# enough that most organisms start as generalists, but with enough spread
# that natural selection has variance to work with from the first generation.
INITIAL_DIET_ACCEPT_CHANCE = 0.7

# Chance mutate() flips exactly one food kind's acceptance on/off.
DIET_MUTATION_CHANCE = 0.15


def _jitter(value: float, rate: float) -> float:
    return max(0.01, value * random.uniform(1 - rate, 1 + rate))


def _jitter_channel(value: int, rate: float) -> int:
    delta = int(value * rate)
    return max(0, min(255, value + random.randint(-delta, delta) if delta else value))


def _mutate_diet(diet: frozenset, rate: float) -> frozenset:
    if random.random() >= rate:
        return diet

    kind = random.choice(FOOD_KINDS)
    mutated = set(diet)
    if kind in mutated:
        mutated.discard(kind)
    else:
        mutated.add(kind)
    return frozenset(mutated)


@dataclass
class Genome:
    """Heritable traits: what a new organism starts with, independent of
    the actual matter its body is built from."""

    speed: float
    max_energy: float
    energy_drain_rate: float
    search_radius: float
    wander_radius: float
    diet: frozenset
    color: tuple

    def crossover(self, other: 'Genome') -> 'Genome':
        return Genome(
            speed=random.choice((self.speed, other.speed)),
            max_energy=random.choice((self.max_energy, other.max_energy)),
            energy_drain_rate=random.choice((self.energy_drain_rate, other.energy_drain_rate)),
            search_radius=random.choice((self.search_radius, other.search_radius)),
            wander_radius=random.choice((self.wander_radius, other.wander_radius)),
            diet=random.choice((self.diet, other.diet)),
            color=random.choice((self.color, other.color)),
        )

    def mutate(self, rate: float = 0.15) -> 'Genome':
        return Genome(
            speed=_jitter(self.speed, rate),
            max_energy=_jitter(self.max_energy, rate),
            energy_drain_rate=_jitter(self.energy_drain_rate, rate),
            search_radius=_jitter(self.search_radius, rate),
            wander_radius=_jitter(self.wander_radius, rate),
            diet=_mutate_diet(self.diet, DIET_MUTATION_CHANCE),
            color=tuple(_jitter_channel(c, rate) for c in self.color),
        )

    @staticmethod
    def random() -> 'Genome':
        return Genome(
            speed=random.uniform(20, 50),
            max_energy=random.uniform(40, 220),
            energy_drain_rate=random.uniform(3, 9),
            search_radius=random.uniform(100, 300),
            wander_radius=random.uniform(30, 150),
            diet=frozenset(k for k in FOOD_KINDS if random.random() < INITIAL_DIET_ACCEPT_CHANCE),
            color=(
                random.randint(150, 255),
                random.randint(200, 255),
                random.randint(0, 100),
            ),
        )
