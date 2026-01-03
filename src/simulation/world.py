import pymunk

from core.organism_factory import OrganismFactory


class World:
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self.space.use_spatial_hash(10, 10000)

        handler = self.space.add_collision_handler(2, 2)
        handler.begin = self.on_collision_begin

        self.organisms = []
        self.objects = []

        for _ in range(10):
            organism = OrganismFactory.create_basic()
            self.add_organism(organism)

    def on_collision_begin(self, arbiter, space, data):
        shape1, shape2 = arbiter.shapes

        return True

    def add_organism(self, organism):
        self.organisms.append(organism)
        self.space.add(organism, organism.shape)

    def update(self, delta_time):
        for organism in self.organisms:
            organism.update()

    def fixed_update(self, delta_time):
        self.space.step(0.1)
