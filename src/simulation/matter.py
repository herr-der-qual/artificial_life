from simulation.elements import Atoms, Elements

class Matter:
    def __init__(self):
        self.elements = []
        self.mass = 0
        self.energy = 0

    def add_element(self, element: Elements):
        self.add_elements([element])

    def add_elements(self, elements):
        self.elements.extend(elements)
        self.mass += self._calculate_mass(elements)
        self.energy += self._calculate_energy(elements)

    def _calculate_mass(self, elements):
        return sum(Atoms[element].mass for element in elements)

    def _calculate_energy(self, elements):
        return sum(Atoms[element].valence * 10 for element in elements)
