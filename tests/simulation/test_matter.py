import pytest

from simulation.elements import Elements
from simulation.matter import Matter
from simulation.molecule import Molecule


def test_mass_sums_across_molecules():
    matter = Matter()

    water = Molecule()
    o = water.add_atom(Elements.O)
    h1 = water.add_atom(Elements.H)
    h2 = water.add_atom(Elements.H)
    water.add_bond(o, h1)
    water.add_bond(o, h2)

    co2 = Molecule()
    c = co2.add_atom(Elements.C)
    o1 = co2.add_atom(Elements.O)
    o2 = co2.add_atom(Elements.O)
    co2.add_bond(c, o1, order=2)
    co2.add_bond(c, o2, order=2)

    matter.add_molecule(water)
    matter.add_molecule(co2)

    assert matter.mass == pytest.approx(water.mass + co2.mass)
    assert matter.stored_energy == pytest.approx(water.bond_energy + co2.bond_energy)


def test_empty_matter_has_no_mass_or_energy():
    matter = Matter()
    assert matter.mass == 0
    assert matter.stored_energy == 0
