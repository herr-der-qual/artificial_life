from simulation.genome import Genome


def make_genome(**overrides):
    defaults = dict(
        speed=30.0, max_energy=100.0, energy_drain_rate=10.0,
        search_radius=200.0, color=(100, 150, 200),
    )
    defaults.update(overrides)
    return Genome(**defaults)


def test_crossover_picks_each_field_from_one_parent():
    a = make_genome(speed=10.0, max_energy=50.0, energy_drain_rate=5.0, search_radius=100.0, color=(0, 0, 0))
    b = make_genome(speed=90.0, max_energy=150.0, energy_drain_rate=15.0, search_radius=300.0, color=(255, 255, 255))

    for _ in range(30):
        child = a.crossover(b)
        assert child.speed in (a.speed, b.speed)
        assert child.max_energy in (a.max_energy, b.max_energy)
        assert child.energy_drain_rate in (a.energy_drain_rate, b.energy_drain_rate)
        assert child.search_radius in (a.search_radius, b.search_radius)
        assert child.color in (a.color, b.color)


def test_mutate_stays_within_rate_bounds():
    genome = make_genome(speed=40.0, max_energy=100.0, energy_drain_rate=10.0)
    rate = 0.15

    for _ in range(50):
        mutated = genome.mutate(rate=rate)
        assert genome.speed * (1 - rate) - 1e-6 <= mutated.speed <= genome.speed * (1 + rate) + 1e-6
        assert genome.max_energy * (1 - rate) - 1e-6 <= mutated.max_energy <= genome.max_energy * (1 + rate) + 1e-6
        assert genome.search_radius * (1 - rate) - 1e-6 <= mutated.search_radius <= genome.search_radius * (1 + rate) + 1e-6


def test_mutate_keeps_color_channels_in_byte_range():
    genome = make_genome(color=(250, 5, 128))

    for _ in range(50):
        mutated = genome.mutate(rate=0.5)
        assert all(0 <= c <= 255 for c in mutated.color)


def test_random_produces_positive_traits():
    for _ in range(20):
        genome = Genome.random()
        assert genome.speed > 0
        assert genome.max_energy > 0
        assert genome.energy_drain_rate > 0
        assert genome.search_radius > 0
        assert len(genome.color) == 3
