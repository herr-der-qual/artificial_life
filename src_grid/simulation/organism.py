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

    Movement doubles as foraging: adjacent food is eaten immediately if
    there is any; otherwise the organism scans out to SEARCH_RADIUS cells
    for the nearest food and steps toward it, falling back to a random
    free direction only once nothing edible is visible at all. Fixed for
    now, not a Genome trait - a simple "smell", not full genetics."""

    # Calibrated in grid ticks (this world has no delta_time), not the
    # pymunk system's seconds - REPRODUCE_MATTER_THRESHOLD is kept the
    # same, though, since it's measured in atomic mass from the same
    # shared chemistry (MoleculeFactory/Reactor), not simulation time.
    REPRODUCE_ENERGY_COST = 30.0
    REPRODUCE_ENERGY_SAFETY_MARGIN = 1.5
    REPRODUCE_MATTER_THRESHOLD = 25.0
    REPRODUCE_COOLDOWN = 10  # ticks

    # How far the organism can "see" food to path toward, in cells -
    # checked every tick it isn't already next to food, via Grid's
    # spatial index (see _nearest_visible_food) rather than a raw square
    # scan, so this can stay generous without costing much even when
    # most of that area is empty.
    SEARCH_RADIUS = 5

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
        move one cell - onto adjacent food if there is any (eating it),
        toward the nearest visible food if there's any within
        SEARCH_RADIUS, or a random free direction if there's nothing
        edible in sight at all. Returns whether it ate."""
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

        nearest = self._nearest_visible_food(grid, col, row)
        if nearest is not None:
            for dc, dr in self._directions_toward(col, row, *nearest):
                candidate = (col + dc, row + dr)
                if grid.is_free(*candidate):
                    grid.move(self, *candidate)
                    return False
            # Both the preferred and the fallback axis are blocked - drop
            # through to the same random wander everyone else gets.

        dc, dr = directions[0]
        grid.move(self, col + dc, row + dr)
        return False

    def _nearest_visible_food(self, grid, col, row):
        """The closest Food (Manhattan distance) within SEARCH_RADIUS
        cells, or None if there isn't one. Grid.nearby_positions() only
        visits occupied cells near (col, row) via its bucket index, not
        every cell in the search square - previously a plain O(radius^2)
        scan regardless of how much of that square was actually empty,
        profiled as the dominant cost in World.update() at a few thousand
        organisms."""
        best, best_distance = None, None
        for candidate in grid.nearby_positions(col, row, self.SEARCH_RADIUS):
            if candidate == (col, row):
                continue
            if not isinstance(grid.occupant_at(*candidate), Food):
                continue
            distance = abs(candidate[0] - col) + abs(candidate[1] - row)
            if best_distance is None or distance < best_distance:
                best, best_distance = candidate, distance
        return best

    @staticmethod
    def _directions_toward(col, row, target_col, target_row) -> list:
        """Single-cell steps that reduce the distance to (target_col,
        target_row), the bigger axis first - e.g. food mostly east and a
        little north tries east before north, falling back to north only
        if east turns out to be blocked."""
        dx, dy = target_col - col, target_row - row
        candidates = []
        if dx != 0:
            candidates.append(((1 if dx > 0 else -1, 0), abs(dx)))
        if dy != 0:
            candidates.append(((0, 1 if dy > 0 else -1), abs(dy)))
        candidates.sort(key=lambda pair: pair[1], reverse=True)
        return [direction for direction, _ in candidates]

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
