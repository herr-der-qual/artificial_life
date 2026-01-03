import pymunk

from simulation.matter import Matter
from simulation.elements import Elements, Atoms
from ai.brain import Brain
from simulation.object import Object

class Organism(Object):
    def __init__(self, matter: Matter, speed=20, energy=100, color=(0, 255, 0)):
        super().__init__(matter, color, body_type = pymunk.Body.KINEMATIC)

        self.brain = Brain(self)
        self.speed = speed
        self.energy = energy

        self.shape.collision_type = 2

    def update(self):
        self.brain.update()
