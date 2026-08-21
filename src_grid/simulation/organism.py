import random

from simulation.matter import Matter
from simulation.reactor import Reactor

from src_grid.simulation.food import Food
from src_grid.simulation.genome import Genome


class Organism:
    """A movable, energy-driven entity on the Grid. No diet/brain yet (see
    the pymunk-based Organism for where those eventually come from once
    this model is proven out) - just enough to prove a real
    energy/eating/death/reproduction/genetics loop works on a discrete
    field. max_energy and energy_drain_rate come from the organism's own
    Genome, not a shared class constant - two organisms can genuinely
    differ now, and reproduction (see OrganismFactory) passes those
    differences on with mutation.

    Movement doubles as foraging: each tick the organism checks its four
    neighboring cells for food first and moves onto it (eating it) if
    there is any, falling back to a random free direction otherwise -
    there's no brain/search radius yet, so "seeking" food only reaches as
    far as the organism can already see from where it's standing."""

    # Calibrated in grid ticks (this world has no delta_time), not the
    # pymunk system's seconds - REPRODUCE_MATTER_THRESHOLD is kept the
    # same, though, since it's measured in atomic mass from the same
    # shared chemistry (MoleculeFactory/Reactor), not simulation time.
    REPRODUCE_ENERGY_COST = 30.0
    REPRODUCE_ENERGY_SAFETY_MARGIN = 1.5
    REPRODUCE_MATTER_THRESHOLD = 25.0
    REPRODUCE_COOLDOWN = 10  # ticks

    _DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def __init__(self, matter: Matter, genome: Genome, energy: float = None, generation: int = 0):
        self.matter = matter
        self.genome = genome
        self.color = genome.color
        self.max_energy = genome.max_energy
        self.energy_drain_rate = genome.energy_drain_rate

        self.position = (0, 0)  # (col, row) - set for real by Grid.place
        self.energy = self.max_energy if energy is None else energy
        self.is_alive = True
        self.generation = generation

        # Leftover atoms from digested food, not yet spent - the
        # biological "cost" reproduction draws from (see can_reproduce).
        self.reserve = Matter()
        self.reproduction_cooldown = 0

    def step(self, grid) -> bool:
        """Drain energy and die of starvation if it runs out; otherwise
        move one cell - onto adjacent food if there is any (eating it), or
        a random free direction otherwise. Returns whether it ate."""
        self.energy -= self.energy_drain_rate
        self.reproduction_cooldown = max(0, self.reproduction_cooldown - 1)
        if self.energy <= 0:
            self.is_alive = False
            return False

        col, row = self.position
        directions = list(self._DIRECTIONS)
        random.shuffle(directions)

        food, target = None, None
        for dc, dr in directions:
            candidate = (col + dc, row + dr)
            occupant = grid.occupant_at(*candidate)
            if isinstance(occupant, Food):
                food, target = occupant, candidate
                break

        if food is not None:
            grid.remove(food)
            grid.move(self, *target)
            self._eat(food)
            return True

        dc, dr = directions[0]
        grid.move(self, col + dc, row + dr)
        return False

    def _eat(self, food: Food):
        """Digest via the same catalyzed reaction the pymunk system uses:
        net energy goes straight to self.energy, and the leftover atoms
        (the reaction's products) are stashed in reserve to fund a future
        reproduction (see can_reproduce)."""
        result = Reactor.react(food.matter.molecules, catalyzed=True)
        self.energy = min(self.max_energy, self.energy + result.energy_delta)
        for product in result.products:
            self.reserve.add_molecule(product)

    def can_reproduce(self) -> bool:
        return (
            self.is_alive
            and self.reproduction_cooldown <= 0
            and self.energy >= self.REPRODUCE_ENERGY_COST * self.REPRODUCE_ENERGY_SAFETY_MARGIN
            and self.reserve.mass >= self.REPRODUCE_MATTER_THRESHOLD
        )
