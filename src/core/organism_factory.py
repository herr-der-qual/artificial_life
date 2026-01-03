import pymunk
import random

from core.organism_builder import OrganismBuilder
from simulation.matter import Matter
from simulation.elements import Elements


class OrganismFactory:
    @staticmethod
    def create_predator():
        pass

    @staticmethod
    def create_prey():
        pass

    @staticmethod
    def create_random():
        builder = OrganismBuilder()
        matter = Matter()

        num_elements = random.randint(2, 5)
        available_elements = [
            Elements.H, Elements.C, Elements.N, Elements.O,
            Elements.P, Elements.S
        ]
        elements = random.choices(available_elements, k=num_elements)
        matter.add_elements(elements)

        speed = random.uniform(20, 50)
        energy = random.uniform(50, 150)
        energy_drain_rate = random.uniform(5, 15)

        color = (
            random.randint(150, 255),  # R
            random.randint(200, 255),  # G
            random.randint(0, 100)     # B
        )
        x = random.uniform(-300, 300)
        y = random.uniform(-300, 300)

        return (
            builder.set_position((x, y))
                .set_speed(speed)
                .set_energy(energy)
                .set_energy_drain_rate(energy_drain_rate)
                .set_color(color)
                .set_matter(matter)
                .build()
        )

    @staticmethod
    def create_basic():
        builder = OrganismBuilder()
        matter = Matter()
        matter.add_elements([Elements.C, Elements.C, Elements.C])

        return (
            builder.set_position((100, 100))
                .set_speed(30)
                .set_color((255, 255, 0))
                .set_matter(matter)
                .build()
        )

    @staticmethod
    def create_from_json(file_path):
        pass
