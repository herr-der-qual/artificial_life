import random

from src_grid.core.world_config import WorldConfig
from src_grid.simulation.grid import Grid
from src_grid.core.food_factory import FoodFactory
from src_grid.core.organism_factory import OrganismFactory


class World:
    """Walking skeleton for the grid rewrite: a discrete field with food
    and organisms on it, organisms random-walking each tick. Deliberately
    minimal and independent of the existing pymunk-based World - real
    movement rules (AI, eating, genetics) come once this much is proven
    out."""

    def __init__(self, config: WorldConfig = None):
        self.config = config or WorldConfig()

        width = self.config.get("width")
        height = self.config.get("height")

        self.grid = Grid(width, height)
        self.organisms = []
        self.tick_count = 0

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
        for organism in self.organisms:
            organism.step(self.grid)
