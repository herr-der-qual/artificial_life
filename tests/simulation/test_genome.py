from simulation.genome import Genome
from simulation.substance import FOOD_KINDS


def make_genome(**overrides):
    defaults = dict(
        speed=30.0, max_energy=100.0, energy_drain_rate=10.0,
        search_radius=200.0, wander_radius=50.0, diet=frozenset(FOOD_KINDS),
        color=(100, 150, 200),
    )
    defaults.update(overrides)
    return Genome(**defaults)


def test_crossover_picks_each_field_from_one_parent():
    a = make_genome(
        speed=10.0, max_energy=50.0, energy_drain_rate=5.0, search_radius=100.0,
        wander_radius=20.0, diet=frozenset({"basic"}), color=(0, 0, 0),
    )
    b = make_genome(
        speed=90.0, max_energy=150.0, energy_drain_rate=15.0, search_radius=300.0,
        wander_radius=140.0, diet=frozenset({"rich", "simple"}), color=(255, 255, 255),
    )

    for _ in range(30):
        child = a.crossover(b)
        assert child.speed in (a.speed, b.speed)
        assert child.max_energy in (a.max_energy, b.max_energy)
        assert child.energy_drain_rate in (a.energy_drain_rate, b.energy_drain_rate)
        assert child.search_radius in (a.search_radius, b.search_radius)
        assert child.wander_radius in (a.wander_radius, b.wander_radius)
        assert child.diet in (a.diet, b.diet)
        assert child.color in (a.color, b.color)


def test_mutate_stays_within_rate_bounds():
    genome = make_genome(speed=40.0, max_energy=100.0, energy_drain_rate=10.0, wander_radius=60.0)
    rate = 0.15

    for _ in range(50):
        mutated = genome.mutate(rate=rate)
        assert genome.speed * (1 - rate) - 1e-6 <= mutated.speed <= genome.speed * (1 + rate) + 1e-6
        assert genome.max_energy * (1 - rate) - 1e-6 <= mutated.max_energy <= genome.max_energy * (1 + rate) + 1e-6
        assert genome.search_radius * (1 - rate) - 1e-6 <= mutated.search_radius <= genome.search_radius * (1 + rate) + 1e-6
        assert genome.wander_radius * (1 - rate) - 1e-6 <= mutated.wander_radius <= genome.wander_radius * (1 + rate) + 1e-6


def test_mutate_keeps_color_channels_in_byte_range():
    genome = make_genome(color=(250, 5, 128))

    for _ in range(50):
        mutated = genome.mutate(rate=0.5)
        assert all(0 <= c <= 255 for c in mutated.color)


def test_mutate_diet_changes_at_most_one_kind():
    genome = make_genome(diet=frozenset({"basic", "rich"}))

    for _ in range(50):
        mutated = genome.mutate()
        assert len(mutated.diet.symmetric_difference(genome.diet)) <= 1
        assert mutated.diet.issubset(frozenset(FOOD_KINDS))


def test_mutate_diet_can_add_and_remove_kinds():
    genome = make_genome(diet=frozenset({"basic"}))

    seen_additions = False
    seen_removals = False
    for _ in range(200):
        mutated = genome.mutate()
        if len(mutated.diet) > len(genome.diet):
            seen_additions = True
        elif len(mutated.diet) < len(genome.diet):
            seen_removals = True

    assert seen_additions
    assert seen_removals


def test_random_produces_positive_traits():
    for _ in range(20):
        genome = Genome.random()
        assert genome.speed > 0
        assert genome.max_energy > 0
        assert genome.energy_drain_rate > 0
        assert genome.search_radius > 0
        assert genome.wander_radius > 0
        assert genome.diet.issubset(frozenset(FOOD_KINDS))
        assert len(genome.color) == 3
