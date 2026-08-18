from simulation.bond import estimate_bond_energy
from simulation.elements import Elements


def test_bond_energy_is_positive():
    assert estimate_bond_energy(Elements.C, Elements.H, 1) > 0


def test_bond_energy_is_symmetric():
    assert estimate_bond_energy(Elements.O, Elements.H, 1) == estimate_bond_energy(Elements.H, Elements.O, 1)


def test_bond_energy_scales_linearly_with_order():
    single = estimate_bond_energy(Elements.C, Elements.O, 1)
    double = estimate_bond_energy(Elements.C, Elements.O, 2)
    assert double == single * 2


def test_polar_bond_stronger_than_nonpolar_of_similar_size():
    # O-H (electronegativity diff 1.24) should beat C-C (diff 0, similar size class)
    polar = estimate_bond_energy(Elements.O, Elements.H, 1)
    nonpolar = estimate_bond_energy(Elements.C, Elements.C, 1)
    assert polar > nonpolar
