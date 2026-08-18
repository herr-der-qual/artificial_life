from simulation.molecule import Molecule


class Matter:
    def __init__(self):
        self.molecules: list[Molecule] = []

    def add_molecule(self, molecule: Molecule):
        self.molecules.append(molecule)

    @property
    def mass(self) -> float:
        return sum(molecule.mass for molecule in self.molecules)

    @property
    def stored_energy(self) -> float:
        return sum(molecule.bond_energy for molecule in self.molecules)
