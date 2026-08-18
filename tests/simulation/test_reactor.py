from simulation.elements import Elements, Atoms
from simulation.molecule import Molecule
from simulation.reactor import Reactor
from core.molecule_factory import MoleculeFactory


def lone_atom(element):
    molecule = Molecule()
    molecule.add_atom(element)
    return molecule


def assert_valence_respected(molecule):
    for atom in molecule.atoms:
        assert atom.used_valence <= Atoms[atom.element].valence


def test_saturated_molecules_do_not_react_without_energy():
    co2 = MoleculeFactory.co2()
    water = MoleculeFactory.water()

    result = Reactor.react([co2, water], available_energy=0.0, catalyzed=False)

    assert result.energy_delta == 0
    assert len(result.products) == 2
    formulas = sorted([p.formula() for p in result.products], key=str)
    assert formulas == sorted([co2.formula(), water.formula()], key=str)


def test_two_free_atoms_combine_and_release_energy():
    h1 = lone_atom(Elements.H)
    h2 = lone_atom(Elements.H)

    result = Reactor.react([h1, h2])

    assert result.energy_delta > 0
    assert len(result.products) == 1
    assert result.products[0].formula() == {Elements.H: 2}


def test_products_never_exceed_valence():
    pool = [Elements.H, Elements.C, Elements.N, Elements.O]
    molecules = [MoleculeFactory.random_molecule(pool, atom_count=4) for _ in range(4)]

    result = Reactor.react(molecules, available_energy=50.0, catalyzed=True)

    for product in result.products:
        assert_valence_respected(product)


def test_reaction_above_atom_cap_is_skipped():
    molecules = [lone_atom(Elements.C) for _ in range(Reactor.MAX_ATOMS_PER_REACTION + 1)]

    result = Reactor.react(molecules)

    assert result.energy_delta == 0
    assert result.products == molecules


def test_digesting_organic_food_yields_net_positive_energy():
    food = MoleculeFactory.simple_organic()

    result = Reactor.react([food], catalyzed=True)

    assert result.energy_delta > 0


def test_digesting_water_does_not_yield_net_energy():
    water = MoleculeFactory.water()

    result = Reactor.react([water], catalyzed=True)

    assert result.energy_delta <= 0


def test_empty_input_is_a_no_op():
    result = Reactor.react([])
    assert result.products == []
    assert result.energy_delta == 0
