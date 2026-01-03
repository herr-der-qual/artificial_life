import pymunk

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
        pass

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
