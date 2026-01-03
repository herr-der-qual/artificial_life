import pymunk

from core.organism_factory import OrganismFactory
from core.substance_factory import SubstanceFactory


class World:
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self.space.use_spatial_hash(10, 10000)

        handler = self.space.add_collision_handler(2, 2)
        handler.begin = self.on_collision_begin

        self.organisms = []
        self.substances = []

        # Spawn organisms
        for _ in range(10):
            organism = OrganismFactory.create_basic()
            self.add_organism(organism)

        # Spawn initial food substances
        for _ in range(50):
            substance = SubstanceFactory.spawn_random_in_bounds()
            self.add_substance(substance)

    def on_collision_begin(self, arbiter, space, data):
        shape1, shape2 = arbiter.shapes

        return True

    def add_organism(self, organism):
        self.organisms.append(organism)
        self.space.add(organism, organism.shape)

    def add_substance(self, substance):
        self.substances.append(substance)
        self.space.add(substance, substance.shape)

    def remove_substance(self, substance):
        if substance in self.substances:
            self.substances.remove(substance)
            self.space.remove(substance, substance.shape)

    def update(self, delta_time):
        for organism in self.organisms:
            organism.update()

    def fixed_update(self, delta_time):
        self.space.step(0.1)
