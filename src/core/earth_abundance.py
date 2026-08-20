import random

from simulation.elements import Elements

# Elemental abundance of Earth's crust by mass (Clarke numbers), restricted
# to elements this project's chemistry can actually use - noble gases
# (valence 0) can't form bonds and are already excluded everywhere else, so
# there's no point weighting them. Real crust also has ~12% Fe/Ca/K/Ti/Mn
# that aren't in our periodic table subset; leaving them out just means the
# supported elements are proportionally a bit more common than in reality,
# not that the relative order/scale is wrong (oxygen and silicon still
# dwarf everything else, same as on the real Earth).
CRUST_ABUNDANCE_PERCENT = {
    Elements.O: 46.6,
    Elements.Si: 27.7,
    Elements.Al: 8.1,
    Elements.Na: 2.8,
    Elements.Mg: 2.1,
    Elements.H: 0.14,
    Elements.P: 0.10,
    Elements.F: 0.06,
    Elements.S: 0.05,
    Elements.C: 0.018,
    Elements.Cl: 0.017,
    Elements.N: 0.002,
    Elements.Li: 0.002,
    Elements.B: 0.001,
}


def weighted_element_pool(size: int = 500) -> list:
    """A pool pre-populated in Earth-crust proportions - pass this to
    MoleculeFactory.random_molecule (which picks uniformly from whatever
    pool it's handed) to get abundance-weighted element selection without
    changing its signature."""
    elements = list(CRUST_ABUNDANCE_PERCENT.keys())
    weights = list(CRUST_ABUNDANCE_PERCENT.values())
    return random.choices(elements, weights=weights, k=size)
