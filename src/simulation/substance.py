from simulation.matter import Matter

import pymunk

class Substance(pymunk.Body):
    def __init__(self, matter: Matter, color, body_type = pymunk.Body.KINEMATIC):
        super().__init__(matter.mass, 1, body_type)
        
        self.shape = pymunk.Poly(self, [(-4, -4), (0, 4), (4, -4)])
        self.shape.collision_type = 1
        self.matter = matter
        self.color = color