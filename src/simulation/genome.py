import random
from dataclasses import dataclass

from simulation.substance import FOOD_KINDS

# Chance any given food kind starts in a fresh random genome's diet - high
# enough that most organisms start as generalists, but with enough spread
# that natural selection has variance to work with from the first generation.
INITIAL_DIET_ACCEPT_CHANCE = 0.7

# "flesh" (predation, see World._resolve_predation) starts far rarer than
# ordinary food kinds - most of the population begins peaceful, and
# predation only spreads from the rare mutant if it's actually a winning
# strategy, rather than plunging every fresh population straight into
# universal cannibalism.
INITIAL_FLESH_ACCEPT_CHANCE = 0.05

# Chance mutate() flips exactly one food kind's acceptance on/off.
DIET_MUTATION_CHANCE = 0.15

# Default strength passed to mutate() - also the baseline discrete chances
# above are calibrated at. A caller passing a different `rate` scales the
# diet/cell_count flip chances by the same ratio, so one number controls
# both continuous jitter and discrete mutation strength together.
BASE_MUTATION_RATE = 0.15

# Sexual reproduction needs two organisms to physically find and reach each
# other - slow and costly compared to solo budding (see Organism.
# can_reproduce_asexually). Its payoff is much stronger variability, so it
# stays worth pursuing as a source of diversity even though asexual budding
# is the fast, primary way generations turn over.
SEXUAL_MUTATION_RATE = 0.4

# Chance mutate() nudges cell_count by +-1. Population starts unicellular
# (Genome.random() always 1) - multicellularity only appears if it's
# actually worth the energy/speed cost (see Organism), an emergent choice
# of selection, not a starting assumption.
CELL_COUNT_MUTATION_CHANCE = 0.15
MIN_CELL_COUNT = 1
MAX_CELL_COUNT = 10


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


def _mutate_cell_count(cell_count: int, rate: float) -> int:
    if random.random() >= rate:
        return cell_count

    delta = random.choice((-1, 1))
    return max(MIN_CELL_COUNT, min(MAX_CELL_COUNT, cell_count + delta))


@dataclass
class Genome:
    """Heritable traits: what a new organism starts with, independent of
    the actual matter its body is built from."""

    speed: float
    max_energy: float
    energy_drain_rate: float
    search_radius: float
    wander_radius: float
    cell_count: int
    diet: frozenset
    color: tuple

    def crossover(self, other: 'Genome') -> 'Genome':
        return Genome(
            speed=random.choice((self.speed, other.speed)),
            max_energy=random.choice((self.max_energy, other.max_energy)),
            energy_drain_rate=random.choice((self.energy_drain_rate, other.energy_drain_rate)),
            search_radius=random.choice((self.search_radius, other.search_radius)),
            wander_radius=random.choice((self.wander_radius, other.wander_radius)),
            cell_count=random.choice((self.cell_count, other.cell_count)),
            diet=random.choice((self.diet, other.diet)),
            color=random.choice((self.color, other.color)),
        )

    def mutate(self, rate: float = BASE_MUTATION_RATE) -> 'Genome':
        discrete_scale = rate / BASE_MUTATION_RATE
        return Genome(
            speed=_jitter(self.speed, rate),
            max_energy=_jitter(self.max_energy, rate),
            energy_drain_rate=_jitter(self.energy_drain_rate, rate),
            search_radius=_jitter(self.search_radius, rate),
            wander_radius=_jitter(self.wander_radius, rate),
            cell_count=_mutate_cell_count(self.cell_count, min(1.0, CELL_COUNT_MUTATION_CHANCE * discrete_scale)),
            diet=_mutate_diet(self.diet, min(1.0, DIET_MUTATION_CHANCE * discrete_scale)),
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
            cell_count=1,
            diet=frozenset(
                k for k in FOOD_KINDS
                if random.random() < (INITIAL_FLESH_ACCEPT_CHANCE if k == "flesh" else INITIAL_DIET_ACCEPT_CHANCE)
            ),
            color=(
                random.randint(150, 255),
                random.randint(200, 255),
                random.randint(0, 100),
            ),
        )
