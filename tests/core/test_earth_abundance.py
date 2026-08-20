from simulation.elements import Atoms
from core.earth_abundance import CRUST_ABUNDANCE_PERCENT, weighted_element_pool


def test_all_abundance_elements_have_positive_valence():
    """Noble gases (valence 0) can't form bonds and are excluded from the
    chemistry everywhere else - weighting them here would be pointless."""
    for element in CRUST_ABUNDANCE_PERCENT:
        assert Atoms[element].valence > 0


def test_oxygen_and_silicon_dominate_the_abundance_table():
    """The whole point of using real Earth-crust numbers: O and Si should
    dwarf everything else, same as on the real planet."""
    total = sum(CRUST_ABUNDANCE_PERCENT.values())
    from simulation.elements import Elements
    o_si_share = (CRUST_ABUNDANCE_PERCENT[Elements.O] + CRUST_ABUNDANCE_PERCENT[Elements.Si]) / total
    assert o_si_share > 0.7


def test_weighted_pool_reflects_real_proportions():
    from simulation.elements import Elements

    pool = weighted_element_pool(size=5000)
    o_count = pool.count(Elements.O)
    n_count = pool.count(Elements.N)

    # oxygen (46.6%) should vastly outnumber nitrogen (0.002%) in the pool
    assert o_count > n_count * 100


def test_weighted_pool_only_contains_known_elements():
    pool = weighted_element_pool(size=200)
    assert set(pool).issubset(set(CRUST_ABUNDANCE_PERCENT.keys()))
