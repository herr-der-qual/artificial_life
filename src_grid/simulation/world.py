import contextlib
import random
import threading

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

        # No upper bound - a big grid costs nothing extra (Grid only
        # stores occupied cells), and how much can actually be spawned
        # onto it is self-limiting (see populate/_random_free_cell: it
        # stops once there's no free cell left, rather than looping
        # forever or spawning some impractical number). Only guards
        # against a nonsensical <= 0 from a hand-edited config.
        width = max(1, self.config.get("width"))
        height = max(1, self.config.get("height"))

        self.grid = Grid(width, height)
        self.organisms = []
        self.tick_count = 0
        self.deaths_count = 0
        self.food_eaten_count = 0
        self.births_count = 0
        self.max_generation_reached = 0

        # populate()/populate_async() fill the grid separately from
        # __init__ - a huge food_count/organism_count can take a while,
        # and callers that want it (see View) run it on a background
        # thread instead of freezing the window for that whole stretch.
        # population_lock guards grid/organisms while that thread is
        # still running; population_done/total are plain ints (safe to
        # read from the main thread without the lock - see populate_async)
        # for a progress readout.
        self.population_lock = threading.Lock()
        self.population_done = 0
        self.population_total = 0
        self.population_complete = True  # nothing populating yet
        self._population_thread = None

    def populate(self):
        """Spawn every configured food/organism, synchronously, on
        whatever thread calls this."""
        self._populate(guard=contextlib.nullcontext())

    def populate_async(self):
        """Same as populate(), but on a background thread - lets View
        show a progress readout and keep the window responsive while a
        large world fills in, instead of freezing until it's done."""
        self.population_complete = False
        self._population_thread = threading.Thread(
            target=self._populate, kwargs={"guard": self.population_lock}, daemon=True,
        )
        self._population_thread.start()

    def _populate(self, guard):
        food_count = max(0, self.config.get("food_count"))
        organism_count = max(0, self.config.get("organism_count"))
        self.population_total = food_count + organism_count
        self.population_done = 0
        self.population_complete = False

        for _ in range(food_count):
            with guard:
                spawned = self._spawn_food()
            if not spawned:
                break  # no free cell left - stop, don't keep trying forever
            self.population_done += 1

        for _ in range(organism_count):
            with guard:
                spawned = self._spawn_organism()
            if not spawned:
                break
            self.population_done += 1

        self.population_complete = True

    def _spawn_food(self) -> bool:
        cell = self._random_free_cell()
        if cell is None:
            return False
        self.grid.place(FoodFactory.create_random(), *cell)
        return True

    def _spawn_organism(self) -> bool:
        cell = self._random_free_cell()
        if cell is None:
            return False
        organism = OrganismFactory.create_random()
        self.grid.place(organism, *cell)
        self.organisms.append(organism)
        return True

    def _random_free_cell(self):
        """None once the grid is completely full - the caller stops
        spawning rather than spinning here forever looking for a cell
        that no longer exists."""
        if len(self.grid) >= self.grid.width * self.grid.height:
            return None

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
