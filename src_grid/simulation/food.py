from simulation.matter import Matter


class Food:
    """A food item living on a Grid - deliberately not a Substance
    (pymunk.Body): the grid rewrite's whole point is a discrete field
    instead of continuous physics, so this carries only what it needs
    (matter/color/kind for chemistry+rendering, an integer (col, row)
    position for the grid) and nothing pymunk-shaped."""

    def __init__(self, matter: Matter, color, kind: str = None):
        self.matter = matter
        self.color = color
        self.kind = kind
        self.position = (0, 0)  # (col, row) - set for real by Grid.place
