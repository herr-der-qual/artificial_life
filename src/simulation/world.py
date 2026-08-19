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

        # The physics dt the NEXT fixed_update() will actually use (see
        # SimulationRunner) - tasks read this while seeking a target so
        # they can clamp velocity and not overshoot past it when the
        # speed slider scales physics_dt way up (see ai/tasks/task.py:
        # seek_velocity). Defaults to a plain, unscaled tick for anything
        # that builds a World without a SimulationRunner (tests, etc).
        self.physics_dt = 1 / 60

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
        self.predation_count = 0
        self.max_generation_reached = 0
        self.food_spawn_timer = 0.0
        self.immigration_timer = 0.0
        self.immigrants_count = 0

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

        # Same double-processing hazard as substances: a collision `begin`
        # can still fire for an organism another callback already killed
        # earlier in this same physics step.
        if organism_a.removed or organism_b.removed:
            return False

        predator, prey = self._resolve_predation(organism_a, organism_b)
        if predator:
            energy_gained = predator.digest(prey.matter)
            predator.energy = min(predator.energy + energy_gained, predator.max_energy)
            prey.die()
            self.remove_organism(prey)
            self.predation_count += 1
            return True

        if organism_a.can_reproduce() and organism_b.can_reproduce():
            child = OrganismFactory.create_offspring(organism_a, organism_b)
            if child:
                self.add_organism(child)
                self.births_count += 1
                self.max_generation_reached = max(self.max_generation_reached, child.generation)

        return True

    def _resolve_predation(self, organism_a, organism_b):
        """Bigger cell_count preys on smaller, if predation is in its
        evolved diet ('flesh' in FOOD_KINDS, see Genome.INITIAL_FLESH_
        ACCEPT_CHANCE). Strict size advantage only - equal-sized organisms
        never prey on each other, and a predator is always eligible prey
        for anything bigger than itself."""
        if "flesh" in organism_a.diet and organism_a.cell_count > organism_b.cell_count:
            return organism_a, organism_b
        if "flesh" in organism_b.diet and organism_b.cell_count > organism_a.cell_count:
            return organism_b, organism_a
        return None, None

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

        self._reproduce_asexually()

        dead_organisms = [org for org in self.organisms if not org.is_alive]
        for organism in dead_organisms:
            corpse = self.convert_organism_to_substance(organism)
            self.add_substance(corpse)
            self.remove_organism(organism)
            self.deaths_count += 1

        self._spawn_food_over_time(delta_time)
        self._rescue_population_if_crashed(delta_time)

    def _reproduce_asexually(self):
        """Budding: any organism eligible on its own (see Organism.
        can_reproduce_asexually) splits off a child immediately, without
        needing to find a mate. This is the primary, fast way generations
        turn over - sexual reproduction (on_organism_collision) stays
        available as a slower, costlier path that pays off in much
        stronger mutation. Snapshot the eligible list first: add_organism
        appends to self.organisms as children are born, and we must not
        iterate that growing list."""
        budding = [org for org in self.organisms if org.can_reproduce_asexually()]
        for parent in budding:
            child = OrganismFactory.create_offspring_asexual(parent)
            if child:
                self.add_organism(child)
                self.births_count += 1
                self.max_generation_reached = max(self.max_generation_reached, child.generation)

    def _rescue_population_if_crashed(self, delta_time):
        """Organisms only ever appear via reproduction - if the population
        ever hits (near) zero there is nothing left to reproduce, a
        permanent dead end no amount of balance tuning avoids (any random
        walk with an absorbing state at 0 gets there eventually). Only
        tops the population back up once it has actually crashed, so it
        doesn't dilute evolution the rest of the time."""
        interval = self.config.get("immigration_check_interval")
        if not interval or interval <= 0:
            return

        self.immigration_timer += delta_time
        if self.immigration_timer < interval:
            return
        self.immigration_timer -= interval

        threshold = self.config.get("min_population_threshold")
        if len(self.organisms) > threshold:
            return

        bound = self.config.get("organism_spawn_bound")
        for _ in range(self.config.get("immigration_count")):
            organism = OrganismFactory.create_random(bound=bound)
            self.add_organism(organism)
            self.immigrants_count += 1

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
        """`delta_time` is the physics dt, not necessarily the metabolism
        dt - callers (see SimulationRunner) deliberately pass a scaled-up
        value so movement stays watchable independent of how fast energy/
        reproduction are actually ticking."""
        self.space.step(delta_time)
