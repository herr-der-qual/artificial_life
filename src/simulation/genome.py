import random
from dataclasses import dataclass


def _jitter(value: float, rate: float) -> float:
    return max(0.01, value * random.uniform(1 - rate, 1 + rate))


def _jitter_channel(value: int, rate: float) -> int:
    delta = int(value * rate)
    return max(0, min(255, value + random.randint(-delta, delta) if delta else value))


@dataclass
class Genome:
    """Heritable traits: what a new organism starts with, independent of
    the actual matter its body is built from."""

    speed: float
    max_energy: float
    energy_drain_rate: float
    search_radius: float
    color: tuple

    def crossover(self, other: 'Genome') -> 'Genome':
        return Genome(
            speed=random.choice((self.speed, other.speed)),
            max_energy=random.choice((self.max_energy, other.max_energy)),
            energy_drain_rate=random.choice((self.energy_drain_rate, other.energy_drain_rate)),
            search_radius=random.choice((self.search_radius, other.search_radius)),
            color=random.choice((self.color, other.color)),
        )

    def mutate(self, rate: float = 0.15) -> 'Genome':
        return Genome(
            speed=_jitter(self.speed, rate),
            max_energy=_jitter(self.max_energy, rate),
            energy_drain_rate=_jitter(self.energy_drain_rate, rate),
            search_radius=_jitter(self.search_radius, rate),
            color=tuple(_jitter_channel(c, rate) for c in self.color),
        )

    @staticmethod
    def random() -> 'Genome':
        return Genome(
            speed=random.uniform(20, 50),
            max_energy=random.uniform(50, 150),
            energy_drain_rate=random.uniform(5, 15),
            search_radius=random.uniform(100, 300),
            color=(
                random.randint(150, 255),
                random.randint(200, 255),
                random.randint(0, 100),
            ),
        )
