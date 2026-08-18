import pytest

from simulation.elements import Elements, Atoms
from simulation.molecule import Molecule


def test_free_valence_decreases_as_bonds_are_added():
    molecule = Molecule()
    o = molecule.add_atom(Elements.O)
    h1 = molecule.add_atom(Elements.H)
    h2 = molecule.add_atom(Elements.H)

    assert o.free_valence == Atoms[Elements.O].valence

    molecule.add_bond(o, h1)
    assert o.free_valence == Atoms[Elements.O].valence - 1
    assert h1.free_valence == 0

    molecule.add_bond(o, h2)
    assert o.free_valence == 0
    assert h2.free_valence == 0


def test_double_bond_consumes_two_valence():
    molecule = Molecule()
    c = molecule.add_atom(Elements.C)
    o = molecule.add_atom(Elements.O)
    molecule.add_bond(c, o, order=2)

    assert c.used_valence == 2
    assert o.used_valence == 2
    assert o.free_valence == 0


def test_mass_sums_atomic_masses():
    molecule = Molecule()
    o = molecule.add_atom(Elements.O)
    h1 = molecule.add_atom(Elements.H)
    h2 = molecule.add_atom(Elements.H)
    molecule.add_bond(o, h1)
    molecule.add_bond(o, h2)

    expected = Atoms[Elements.O].mass + 2 * Atoms[Elements.H].mass
    assert molecule.mass == pytest.approx(expected)


def test_formula_counts_elements():
    molecule = Molecule()
    c = molecule.add_atom(Elements.C)
    o1 = molecule.add_atom(Elements.O)
    o2 = molecule.add_atom(Elements.O)
    molecule.add_bond(c, o1, order=2)
    molecule.add_bond(c, o2, order=2)

    assert molecule.formula() == {Elements.C: 1, Elements.O: 2}


def test_connected_molecule_has_single_component():
    molecule = Molecule()
    o = molecule.add_atom(Elements.O)
    h1 = molecule.add_atom(Elements.H)
    h2 = molecule.add_atom(Elements.H)
    molecule.add_bond(o, h1)
    molecule.add_bond(o, h2)

    components = molecule.connected_components()
    assert len(components) == 1
    assert len(components[0].atoms) == 3


def test_disconnected_atoms_split_into_separate_components():
    molecule = Molecule()
    o = molecule.add_atom(Elements.O)
    h1 = molecule.add_atom(Elements.H)
    h2 = molecule.add_atom(Elements.H)
    molecule.add_bond(o, h1)
    # h2 is never bonded - stays a lone fragment

    components = molecule.connected_components()
    sizes = sorted(len(c.atoms) for c in components)
    assert sizes == [1, 2]
