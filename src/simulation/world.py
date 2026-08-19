import pymunk

from core.organism_factory import OrganismFactory
from core.substance_factory import SubstanceFactory
from core.world_config import WorldConfig
from simulation.substance import Substance
from simulation.matter import Matter
from simulation.reactor import Reactor


class World:
    def __init__(self, config: WorldConfig = None):
        self.config = config or WorldConfig()

        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self.space.use_spatial_hash(10, 10000)

        handler = self.space.add_collision_handler(2, 2)
        handler.begin = self.on_organism_collision

        food_handler = self.space.add_collision_handler(2, 1)
        food_handler.begin = self.on_organism_eat_substance

        chemistry_handler = self.space.add_collision_handler(1, 1)
        chemistry_handler.begin = self.on_substance_collision

        self.organisms = []
        self.substances = []

        self.total_organisms_count = 0
        self.deaths_count = 0
        self.births_count = 0
        self.food_eaten_count = 0
        self.max_generation_reached = 0

        organism_bound = self.config.get("organism_spawn_bound")
        for _ in range(self.config.get("initial_organism_count")):
            organism = OrganismFactory.create_random(bound=organism_bound)
            self.add_organism(organism)

        # Spawn initial food substances
        substance_bound = self.config.get("substance_spawn_bound")
        for _ in range(self.config.get("initial_substance_count")):
            substance = SubstanceFactory.spawn_random_in_bounds(
                -substance_bound, substance_bound, -substance_bound, substance_bound,
            )
            self.add_substance(substance)

    def on_organism_collision(self, arbiter, space, data):
        shape1, shape2 = arbiter.shapes

        organism_a = next((o for o in self.organisms if o == shape1.body), None)
        organism_b = next((o for o in self.organisms if o == shape2.body), None)

        if organism_a and organism_b and organism_a.can_reproduce() and organism_b.can_reproduce():
            child = OrganismFactory.create_offspring(organism_a, organism_b)
            if child:
                self.add_organism(child)
                self.births_count += 1
                self.max_generation_reached = max(self.max_generation_reached, child.generation)

        return True

    def on_organism_eat_substance(self, arbiter, space, data):
        shape1, shape2 = arbiter.shapes

        organism_body = shape1.body if shape1.collision_type == 2 else shape2.body
        substance_body = shape2.body if shape2.collision_type == 1 else shape1.body

        organism = next((o for o in self.organisms if o == organism_body), None)
        substance = next((s for s in self.substances if s == substance_body), None)

        if organism and substance and organism.is_alive:
            energy_gained = organism.digest(substance.matter)
            organism.energy = min(organism.energy + energy_gained, organism.max_energy)

            self.remove_substance(substance)
            self.food_eaten_count += 1

        return False

    def on_substance_collision(self, arbiter, space, data):
        shape1, shape2 = arbiter.shapes

        substance_a = next((s for s in self.substances if s == shape1.body), None)
        substance_b = next((s for s in self.substances if s == shape2.body), None)

        if not substance_a or not substance_b or substance_a is substance_b:
            return True

        molecules = substance_a.matter.molecules + substance_b.matter.molecules
        result = Reactor.react(molecules)

        # Uncatalyzed free-chemistry reactions never break bonds (no available
        # energy), so a positive delta means new bonds actually formed.
        if result.energy_delta <= 0:
            return True

        position = substance_a.position
        self.remove_substance(substance_a)
        self.remove_substance(substance_b)

        for product in result.products:
            product_matter = Matter()
            product_matter.add_molecule(product)

            new_substance = Substance(product_matter, color=SubstanceFactory.color_for(product_matter))
            new_substance.position = position
            self.add_substance(new_substance)

        return False

    def add_organism(self, organism):
        self.organisms.append(organism)
        self.space.add(organism, organism.shape)
        organism.brain.world = self
        self.total_organisms_count += 1

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
            self.deaths_count += 1

    def fixed_update(self, delta_time):
        self.space.step(0.1)
