from simulation.matter import Matter

import pymunk

# The finite set of "kinds" a substance can be tagged as - what an
# organism's Genome.diet references to decide whether it's willing to eat
# a given substance. FOOD_KINDS in genome.py must stay in sync with this.
FOOD_KINDS = ("basic", "rich", "simple", "corpse", "reaction_product")


class Substance(pymunk.Body):
    def __init__(self, matter: Matter, color, body_type = pymunk.Body.KINEMATIC, kind: str = None):
        super().__init__(matter.mass, 1, body_type)

        self.shape = pymunk.Poly(self, [(-4, -4), (0, 4), (4, -4)])
        self.shape.collision_type = 1
        self.matter = matter
        self.color = color
        self.kind = kind
        # Cheap O(1) "is this still in the world" check for tasks caching a
        # target across frames, instead of an O(n) `in world.substances`.
        self.removed = False