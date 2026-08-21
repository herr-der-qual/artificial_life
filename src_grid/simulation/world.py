import random

from src_grid.core.world_config import WorldConfig
from src_grid.simulation.grid import Grid
from src_grid.simulation.food import Food
from src_grid.core.food_factory import FoodFactory
from src_grid.core.organism_factory import OrganismFactory


class World:
    """Walking skeleton for the grid rewrite: a discrete field with food
    and organisms on it, organisms random-walking each tick. Deliberately
    minimal and independent of the existing pymunk-based World - real
    movement rules (AI, eating, genetics) come once this much is proven
    out."""

    CORPSE_COLOR = (150, 150, 150)  # matches the pymunk system's corpse color

    def __init__(self, config: WorldConfig = None):
        self.config = config or WorldConfig()

        width = self.config.get("width")
        height = self.config.get("height")

        self.grid = Grid(width, height)
        self.organisms = []
        self.tick_count = 0
        self.deaths_count = 0
        self.food_eaten_count = 0
        self.births_count = 0
        self.max_generation_reached = 0

        food_count = self.config.get("food_count")
        for _ in range(min(food_count, width * height)):
            self._spawn_food()

        organism_count = self.config.get("organism_count")
        for _ in range(min(organism_count, width * height - len(self.grid))):
            self._spawn_organism()

    def _spawn_food(self):
        col, row = self._random_free_cell()
        self.grid.place(FoodFactory.create_random(), col, row)

    def _spawn_organism(self):
        col, row = self._random_free_cell()
        organism = OrganismFactory.create_random()
        self.grid.place(organism, col, row)
        self.organisms.append(organism)

    def _random_free_cell(self) -> tuple:
        while True:
            col = random.randrange(self.grid.width)
            row = random.randrange(self.grid.height)
            if self.grid.is_free(col, row):
                return col, row

    def update(self):
        self.tick_count += 1
        # Snapshot first - reproduction appends new organisms to
        # self.organisms as we go, and a growing list must not be iterated
        # while it grows (children act starting next tick, not this one).
        for organism in list(self.organisms):
            ate = organism.step(self.grid)
            if ate:
                self.food_eaten_count += 1
            if not organism.is_alive:
                self._handle_death(organism)
                continue
            self._try_reproduce(organism)

    def _try_reproduce(self, parent):
        if not parent.can_reproduce():
            return

        cell = self._free_neighbor_cell(parent.position)
        if cell is None:
            return

        child = OrganismFactory.create_offspring_asexual(parent)
        if child is None:
            return

        self.grid.place(child, *cell)
        self.organisms.append(child)
        self.births_count += 1
        self.max_generation_reached = max(self.max_generation_reached, child.generation)

    def _free_neighbor_cell(self, position):
        col, row = position
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(directions)
        for dc, dr in directions:
            candidate = (col + dc, row + dr)
            if self.grid.is_free(*candidate):
                return candidate
        return None

    def _handle_death(self, organism):
        """A dead organism leaves behind what it was made of - a corpse
        (Food, kind="corpse") built from its own matter, sitting right
        where it died, rather than just vanishing."""
        col, row = organism.position
        self.grid.remove(organism)
        self.organisms.remove(organism)

        corpse = Food(organism.matter, color=self.CORPSE_COLOR, kind="corpse")
        self.grid.place(corpse, col, row)

        self.deaths_count += 1
