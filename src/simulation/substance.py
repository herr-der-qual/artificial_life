from simulation.matter import Matter
from simulation.body_geometry import body_hull

import pymunk

# The finite set of "kinds" a substance can be tagged as - what an
# organism's Genome.diet references to decide whether it's willing to eat
# a given substance. FOOD_KINDS in genome.py must stay in sync with this.
# "flesh" is special: no Substance ever carries that kind - it's reused as
# the diet vocabulary entry that gates live predation (World._resolve_
# predation), not scavenging a Substance.
FOOD_KINDS = ("basic", "rich", "simple", "mineral", "corpse", "reaction_product", "flesh")


class Substance(pymunk.Body):
    def __init__(self, matter: Matter, color, body_type = pymunk.Body.KINEMATIC, kind: str = None,
                 scale: float = 1.0):
        super().__init__(matter.mass, 1, body_type)

        # Body shape is a convex hull (pymunk.Poly requires convex) around
        # the body's actual atoms, not a uniformly scaled placeholder - see
        # body_geometry.body_hull.
        vertices = body_hull(matter.molecules, scale)
        self.shape = pymunk.Poly(self, vertices)
        self.shape.collision_type = 1
        self.matter = matter
        self.color = color
        self.kind = kind
        self.scale = scale
        # Cheap O(1) "is this still in the world" check for tasks caching a
        # target across frames, instead of an O(n) `in world.substances`.
        self.removed = False