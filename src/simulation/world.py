import math

import pymunk

from core.organism_factory import OrganismFactory
from core.substance_factory import SubstanceFactory
from core.world_config import WorldConfig
from simulation.substance import Substance
from simulation.matter import Matter
from simulation.reactor import Reactor


def grid_position(index: int, count: int, bound: float) -> tuple:
    """Position `index` (0-based) of `count` evenly-spaced points on a
    square grid filling [-bound, bound]^2. Used to spawn organisms without
    overlap - random placement can stack many of them on top of each other
    at high counts, causing a burst of spurious collisions (and even
    reproductions) in the very first physics step."""
    columns = math.ceil(math.sqrt(count))
    rows = math.ceil(count / columns)

    col = index % columns
    row = index // columns

    cell_width = (2 * bound) / columns
    cell_height = (2 * bound) / rows

    x = -bound + (col + 0.5) * cell_width
    y = -bound + (row + 0.5) * cell_height
    return x, y


class World:
    def __init__(self, config: WorldConfig = None):
        self.config = config or WorldConfig()

        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        # Was use_spatial_hash(10, 10000) - a fixed cell size tuned for one
        # density. Our configs span wildly different scales (bound 300 to
        # 6000+, thousands of entities packed tight or spread out), so a
        # fixed grid is well-tuned for at most one of them. pymunk's default
        # BB-tree adapts to whatever density is actually there instead.

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
        self.food_spawn_timer = 0.0

        organism_bound = self.config.get("organism_spawn_bound")
        organism_count = self.config.get("initial_organism_count")
        for i in range(organism_count):
            organism = OrganismFactory.create_random(bound=organism_bound)
            organism.position = grid_position(i, organism_count, organism_bound)
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

        # shape.body IS the Organism (Organism subclasses pymunk.Body) - no
        # need to search self.organisms for it, that was an O(n) scan on
        # every single collision and dominates at a few hundred+ organisms.
        organism_a = shape1.body
        organism_b = shape2.body

        if organism_a.can_reproduce() and organism_b.can_reproduce():
            child = OrganismFactory.create_offspring(organism_a, organism_b)
            if child:
                self.add_organism(child)
                self.births_count += 1
                self.max_generation_reached = max(self.max_generation_reached, child.generation)

        return True

    def on_organism_eat_substance(self, arbiter, space, data):
        shape1, shape2 = arbiter.shapes

        organism = shape1.body if shape1.collision_type == 2 else shape2.body
        substance = shape2.body if shape2.collision_type == 1 else shape1.body

        # At high density the same substance can be hit by more than one
        # collision `begin` callback within a single physics step, before
        # its removal actually takes effect - without this guard it gets
        # digested twice, and the second pass tries to break bonds already
        # broken by the first (ValueError: list.remove(x): x not in list).
        if substance.removed:
            return False

        if organism.is_alive:
            if substance.kind not in organism.diet:
                # Evolved dietary preference: the organism won't touch this
                # kind of food at all - just leave it be.
                return False

            energy_gained = organism.digest(substance.matter)
            organism.energy = min(organism.energy + energy_gained, organism.max_energy)

            self.remove_substance(substance)
            self.food_eaten_count += 1

        return False

    def on_substance_collision(self, arbiter, space, data):
        shape1, shape2 = arbiter.shapes

        substance_a = shape1.body
        substance_b = shape2.body

        # Same double-processing hazard as on_organism_eat_substance: either
        # side may have already reacted away in another callback this step.
        if substance_a is substance_b or substance_a.removed or substance_b.removed:
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

            new_substance = Substance(
                product_matter, color=SubstanceFactory.color_for(product_matter), kind="reaction_product",
            )
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
            substance.removed = True

    def remove_organism(self, organism):
        if organism in self.organisms:
            self.organisms.remove(organism)
            self.space.remove(organism, organism.shape)
            organism.removed = True

    def convert_organism_to_substance(self, organism):
        corpse = Substance(
            organism.matter, color=(150, 150, 150), body_type=pymunk.Body.STATIC, kind="corpse",
        )
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

        self._spawn_food_over_time(delta_time)

    def _spawn_food_over_time(self, delta_time):
        interval = self.config.get("food_spawn_interval")
        if not interval or interval <= 0:
            return

        max_substances = self.config.get("max_substance_count")
        if max_substances and len(self.substances) >= max_substances:
            return

        self.food_spawn_timer += delta_time
        if self.food_spawn_timer < interval:
            return
        self.food_spawn_timer -= interval

        bound = self.config.get("substance_spawn_bound")
        for _ in range(self.config.get("food_spawn_count")):
            if max_substances and len(self.substances) >= max_substances:
                break
            substance = SubstanceFactory.spawn_random_in_bounds(-bound, bound, -bound, bound)
            self.add_substance(substance)

    def fixed_update(self, delta_time):
        self.space.step(0.1)
