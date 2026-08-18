from simulation.elements import Atoms, Elements

BASE_BOND_ENERGY = 40.0


def estimate_bond_energy(element_a: Elements, element_b: Elements, order: int = 1) -> float:
    """Procedurally estimate bond strength from valence-shell properties.

    Not a lookup of real bond dissociation energies - derived from
    electronegativity (polarity) and atomic radius (bond length) so that
    relative ordering stays plausible (e.g. O-H stronger than C-C) without
    hand-tuning a table for every element pair.
    """
    atom_a = Atoms[element_a]
    atom_b = Atoms[element_b]

    avg_electronegativity = (atom_a.electron_gativity + atom_b.electron_gativity) / 2
    electronegativity_diff = abs(atom_a.electron_gativity - atom_b.electron_gativity)
    size_factor = 100 / (atom_a.radius + atom_b.radius)

    base = BASE_BOND_ENERGY * avg_electronegativity * size_factor
    polarity_bonus = 1 + electronegativity_diff * 0.5

    return base * polarity_bonus * order


class Bond:
    def __init__(self, atom_a: 'MoleculeAtom', atom_b: 'MoleculeAtom', order: int = 1):
        self.atom_a = atom_a
        self.atom_b = atom_b
        self.order = order

    @property
    def energy(self) -> float:
        return estimate_bond_energy(self.atom_a.element, self.atom_b.element, self.order)

    def other(self, atom: 'MoleculeAtom') -> 'MoleculeAtom':
        return self.atom_b if atom is self.atom_a else self.atom_a
