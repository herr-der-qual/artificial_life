import pymunk

from ai.brain import Brain
from simulation.genome import Genome
from simulation.matter import Matter
from simulation.substance import Substance
from simulation.reactor import Reactor


class Organism(Substance):
    REPRODUCE_ENERGY_COST = 40.0
    REPRODUCE_ENERGY_SAFETY_MARGIN = 1.5
    REPRODUCE_MATTER_THRESHOLD = 25.0
    REPRODUCE_COOLDOWN = 4.0

    # Asexual budding pays the full reproductive cost alone - no partner to
    # split it with - so it needs roughly what sexual reproduction spends in
    # total across both parents, not just one parent's share.
    ASEXUAL_ENERGY_COST = REPRODUCE_ENERGY_COST * 2.0
    ASEXUAL_MATTER_THRESHOLD = REPRODUCE_MATTER_THRESHOLD * 2.0

    # Multicellularity trade-off: each extra cell (beyond the first) grows
    # the energy reserve but costs more to run and slows the body down - so
    # cell_count only spreads if the trade is actually worth it (e.g. the
    # size advantage predation gives, see World._resolve_predation), not a
    # free win handed out by the gene alone.
    CELL_ENERGY_BONUS_PER_CELL = 0.5
    CELL_DRAIN_PENALTY_PER_CELL = 0.3
    CELL_SPEED_PENALTY_PER_CELL = 0.2
    CELL_SIZE_SCALE_PER_CELL = 0.3

    def __init__(self, matter: Matter, genome: Genome, starting_energy: float = None, generation: int = 0):
        extra_cells = genome.cell_count - 1
        scale = 1 + self.CELL_SIZE_SCALE_PER_CELL * extra_cells

        super().__init__(matter, genome.color, body_type=pymunk.Body.KINEMATIC, scale=scale)

        self.genome = genome
        self.brain = Brain(self)
        self.cell_count = genome.cell_count
        self.max_energy = genome.max_energy * (1 + self.CELL_ENERGY_BONUS_PER_CELL * extra_cells)
        self.energy = self.max_energy if starting_energy is None else starting_energy
        self.energy_drain_rate = genome.energy_drain_rate * (1 + self.CELL_DRAIN_PENALTY_PER_CELL * extra_cells)
        self.speed = genome.speed / (1 + self.CELL_SPEED_PENALTY_PER_CELL * extra_cells)
        self.search_radius = genome.search_radius
        self.wander_radius = genome.wander_radius
        self.diet = genome.diet
        self.generation = generation
        self.is_alive = True
        self.shape.collision_type = 2

        # Leftover atoms from digested food that haven't been spent yet -
        # the biological "cost" reproduction draws from.
        self.reserve = Matter()
        self.reproduction_cooldown = 0.0

    def update(self, delta_time=1 / 60):
        if not self.is_alive:
            return

        self.energy -= self.energy_drain_rate * delta_time
        self.reproduction_cooldown = max(0.0, self.reproduction_cooldown - delta_time)

        if self.energy <= 0:
            self.die()
            return

        self.brain.update()

    def die(self):
        self.is_alive = False
        self.energy = 0

    def digest(self, matter: Matter) -> float:
        """Break down eaten matter via the organism's metabolism (a
        catalyzed reaction: digestive enzymes make otherwise costly bonds
        cheap to break), stash the leftover atoms in reserve for future
        reproduction, and return the net energy released."""
        result = Reactor.react(matter.molecules, catalyzed=True)
        for product in result.products:
            self.reserve.add_molecule(product)
        return result.energy_delta

    def can_reproduce(self) -> bool:
        return (
            self.is_alive
            and self.reproduction_cooldown <= 0
            and self.energy >= self.REPRODUCE_ENERGY_COST * self.REPRODUCE_ENERGY_SAFETY_MARGIN
            and self.reserve.mass >= self.REPRODUCE_MATTER_THRESHOLD
        )

    def can_reproduce_asexually(self) -> bool:
        return (
            self.is_alive
            and self.reproduction_cooldown <= 0
            and self.energy >= self.ASEXUAL_ENERGY_COST * self.REPRODUCE_ENERGY_SAFETY_MARGIN
            and self.reserve.mass >= self.ASEXUAL_MATTER_THRESHOLD
        )
