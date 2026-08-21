import random

from simulation.matter import Matter


class Organism:
    """A movable entity on the Grid - deliberately minimal for now, no
    genetics/diet/energy yet (see the pymunk-based Organism for where
    those eventually come from once this model is proven out). Just
    enough to prove movement works on a discrete field."""

    def __init__(self, matter: Matter, color):
        self.matter = matter
        self.color = color
        self.position = (0, 0)  # (col, row) - set for real by Grid.place

    def step(self, grid):
        """Random-walk one cell in one of the 4 cardinal directions. A
        blocked move (something already there, or off the edge) is just a
        no-op this tick, not an error - Grid.move() already guarantees
        two things never share a cell."""
        col, row = self.position
        dc, dr = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        grid.move(self, col + dc, row + dr)
