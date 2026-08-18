import pytest

from simulation.elements import Elements, Atoms
from core.molecule_factory import MoleculeFactory


def assert_valence_respected(molecule):
    for atom in molecule.atoms:
        assert atom.used_valence <= Atoms[atom.element].valence


@pytest.mark.parametrize("builder,expected_formula", [
    (MoleculeFactory.water, {Elements.O: 1, Elements.H: 2}),
    (MoleculeFactory.co2, {Elements.C: 1, Elements.O: 2}),
    (MoleculeFactory.methane, {Elements.C: 1, Elements.H: 4}),
    (MoleculeFactory.ammonia, {Elements.N: 1, Elements.H: 3}),
    (MoleculeFactory.simple_organic, {Elements.C: 1, Elements.O: 1, Elements.H: 2}),
])
def test_known_molecules_have_expected_formula(builder, expected_formula):
    molecule = builder()
    assert molecule.formula() == expected_formula


@pytest.mark.parametrize("builder", [
    MoleculeFactory.water,
    MoleculeFactory.co2,
    MoleculeFactory.methane,
    MoleculeFactory.ammonia,
    MoleculeFactory.simple_organic,
])
def test_known_molecules_are_fully_saturated(builder):
    molecule = builder()
    assert_valence_respected(molecule)
    assert all(atom.free_valence == 0 for atom in molecule.atoms)


@pytest.mark.parametrize("builder", [
    MoleculeFactory.water,
    MoleculeFactory.co2,
    MoleculeFactory.methane,
    MoleculeFactory.ammonia,
    MoleculeFactory.simple_organic,
])
def test_known_molecules_are_single_connected_component(builder):
    molecule = builder()
    assert len(molecule.connected_components()) == 1


def test_random_molecule_respects_valence():
    pool = [Elements.H, Elements.C, Elements.N, Elements.O, Elements.P, Elements.S]

    for _ in range(50):
        molecule = MoleculeFactory.random_molecule(pool, atom_count=6)
        assert_valence_respected(molecule)
        assert 1 <= len(molecule.atoms) <= 6


def test_random_molecule_is_connected():
    pool = [Elements.H, Elements.C, Elements.N, Elements.O]

    for _ in range(20):
        molecule = MoleculeFactory.random_molecule(pool, atom_count=5)
        assert len(molecule.connected_components()) == 1


def test_random_molecule_with_single_atom_count_has_one_atom():
    molecule = MoleculeFactory.random_molecule([Elements.C], atom_count=1)
    assert len(molecule.atoms) == 1
    assert len(molecule.bonds) == 0
