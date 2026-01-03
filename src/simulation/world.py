import pymunk

from core.organism_factory import OrganismFactory
from core.substance_factory import SubstanceFactory
from simulation.substance import Substance


class World:
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self.space.use_spatial_hash(10, 10000)

        handler = self.space.add_collision_handler(2, 2)
        handler.begin = self.on_organism_collision

        food_handler = self.space.add_collision_handler(2, 1)
        food_handler.begin = self.on_organism_eat_substance

        self.organisms = []
        self.substances = []

        for _ in range(10):
            organism = OrganismFactory.create_random()
            self.add_organism(organism)

        # Spawn initial food substances
        for _ in range(50):
            substance = SubstanceFactory.spawn_random_in_bounds()
            self.add_substance(substance)

    def on_organism_collision(self, arbiter, space, data):
        shape1, shape2 = arbiter.shapes
        return True

    def on_organism_eat_substance(self, arbiter, space, data):
        shape1, shape2 = arbiter.shapes

        organism_body = shape1.body if shape1.collision_type == 2 else shape2.body
        substance_body = shape2.body if shape2.collision_type == 1 else shape1.body

        organism = next((o for o in self.organisms if o == organism_body), None)
        substance = next((s for s in self.substances if s == substance_body), None)

        if organism and substance and organism.is_alive:
            energy_gained = substance.matter.energy
            organism.energy = min(organism.energy + energy_gained, organism.max_energy)

            self.remove_substance(substance)

        return False

    def add_organism(self, organism):
        self.organisms.append(organism)
        self.space.add(organism, organism.shape)
        organism.brain.world = self

    def add_substance(self, substance):
        self.substances.append(substance)
        self.space.add(substance, substance.shape)

    def remove_substance(self, substance):
        if substance in self.substances:
            self.substances.remove(substance)
            self.space.remove(substance, substance.shape)

    def remove_organism(self, organism):
        if organism in self.organisms:
            self.organisms.remove(organism)
            self.space.remove(organism, organism.shape)

    def convert_organism_to_substance(self, organism):
        corpse = Substance(organism.matter, color=(150, 150, 150), body_type=pymunk.Body.STATIC)
        corpse.position = organism.position
        corpse.shape.collision_type = 1

        return corpse

    def update(self, delta_time):
        for organism in self.organisms:
            organism.update(delta_time)

        dead_organisms = [org for org in self.organisms if not org.is_alive]
        for organism in dead_organisms:
            corpse = self.convert_organism_to_substance(organism)
            self.add_substance(corpse)
            self.remove_organism(organism)

    def fixed_update(self, delta_time):
        self.space.step(0.1)
