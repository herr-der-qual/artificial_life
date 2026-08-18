import random

from simulation.elements import Atoms, Elements
from simulation.molecule import Molecule


class MoleculeFactory:
    """Builds small molecules with real, valence-correct bonds."""

    @staticmethod
    def water() -> Molecule:
        molecule = Molecule()
        o = molecule.add_atom(Elements.O)
        h1 = molecule.add_atom(Elements.H)
        h2 = molecule.add_atom(Elements.H)
        molecule.add_bond(o, h1)
        molecule.add_bond(o, h2)
        return molecule

    @staticmethod
    def co2() -> Molecule:
        molecule = Molecule()
        c = molecule.add_atom(Elements.C)
        o1 = molecule.add_atom(Elements.O)
        o2 = molecule.add_atom(Elements.O)
        molecule.add_bond(c, o1, order=2)
        molecule.add_bond(c, o2, order=2)
        return molecule

    @staticmethod
    def methane() -> Molecule:
        molecule = Molecule()
        c = molecule.add_atom(Elements.C)
        for _ in range(4):
            h = molecule.add_atom(Elements.H)
            molecule.add_bond(c, h)
        return molecule

    @staticmethod
    def ammonia() -> Molecule:
        molecule = Molecule()
        n = molecule.add_atom(Elements.N)
        for _ in range(3):
            h = molecule.add_atom(Elements.H)
            molecule.add_bond(n, h)
        return molecule

    @staticmethod
    def simple_organic() -> Molecule:
        """Formaldehyde-like CH2O - a small energy-rich organic food molecule."""
        molecule = Molecule()
        c = molecule.add_atom(Elements.C)
        o = molecule.add_atom(Elements.O)
        h1 = molecule.add_atom(Elements.H)
        h2 = molecule.add_atom(Elements.H)
        molecule.add_bond(c, o, order=2)
        molecule.add_bond(c, h1)
        molecule.add_bond(c, h2)
        return molecule

    @staticmethod
    def random_molecule(element_pool: list[Elements], atom_count: int) -> Molecule:
        """Greedily grows a connected, valence-respecting molecule by
        attaching new atoms to a random open-valence atom already in it."""
        molecule = Molecule()
        atoms = [molecule.add_atom(random.choice(element_pool))]

        for _ in range(atom_count - 1):
            open_atoms = [atom for atom in atoms if atom.free_valence > 0]
            if not open_atoms:
                break

            candidates = [element for element in element_pool if Atoms[element].valence > 0]
            if not candidates:
                break

            anchor = random.choice(open_atoms)
            element = random.choice(candidates)
            new_atom = molecule.add_atom(element)

            order = min(anchor.free_valence, Atoms[element].valence, random.choice((1, 1, 1, 2)))
            molecule.add_bond(anchor, new_atom, order=order)
            atoms.append(new_atom)

        return molecule
