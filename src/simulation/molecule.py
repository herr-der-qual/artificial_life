from simulation.elements import Atoms, Elements
from simulation.bond import Bond


class MoleculeAtom:
    def __init__(self, element: Elements):
        self.element = element
        self.bonds: list[Bond] = []

    @property
    def used_valence(self) -> int:
        return sum(bond.order for bond in self.bonds)

    @property
    def free_valence(self) -> int:
        return max(0, Atoms[self.element].valence - self.used_valence)

    def other(self, bond: Bond) -> 'MoleculeAtom':
        return bond.other(self)


class Molecule:
    def __init__(self):
        self.atoms: list[MoleculeAtom] = []
        self.bonds: list[Bond] = []

    def add_atom(self, element: Elements) -> MoleculeAtom:
        atom = MoleculeAtom(element)
        self.atoms.append(atom)
        return atom

    def add_bond(self, atom_a: MoleculeAtom, atom_b: MoleculeAtom, order: int = 1) -> Bond:
        bond = Bond(atom_a, atom_b, order)
        atom_a.bonds.append(bond)
        atom_b.bonds.append(bond)
        self.bonds.append(bond)
        return bond

    @property
    def mass(self) -> float:
        return sum(Atoms[atom.element].mass for atom in self.atoms)

    @property
    def bond_energy(self) -> float:
        return sum(bond.energy for bond in self.bonds)

    def formula(self) -> dict:
        counts = {}
        for atom in self.atoms:
            counts[atom.element] = counts.get(atom.element, 0) + 1
        return counts

    def connected_components(self) -> list['Molecule']:
        """Split this atom/bond graph into separate Molecules wherever it
        isn't connected - used after a reaction breaks bonds apart."""
        visited = set()
        components = []

        for start in self.atoms:
            if start in visited:
                continue

            component_atoms = []
            stack = [start]
            visited.add(start)
            while stack:
                atom = stack.pop()
                component_atoms.append(atom)
                for bond in atom.bonds:
                    neighbor = atom.other(bond)
                    if neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)

            component_set = set(component_atoms)
            molecule = Molecule()
            molecule.atoms = component_atoms
            molecule.bonds = [
                bond for bond in self.bonds
                if bond.atom_a in component_set and bond.atom_b in component_set
            ]
            components.append(molecule)

        return components
