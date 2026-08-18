import pymunk

from ai.brain import Brain
from simulation.matter import Matter
from simulation.substance import Substance
from simulation.reactor import Reactor


class Organism(Substance):
    def __init__(self, matter: Matter, speed=20, energy=100, color=(0, 255, 0)):
        super().__init__(matter, color, body_type = pymunk.Body.KINEMATIC)

        self.brain = Brain(self)
        self.speed = speed
        self.energy = energy
        self.max_energy = energy
        self.is_alive = True
        self.energy_drain_rate = 10
        self.shape.collision_type = 2

    def update(self, delta_time=1/60):
        if not self.is_alive:
            return

        self.energy -= self.energy_drain_rate * delta_time

        if self.energy <= 0:
            self.die()
            return

        self.brain.update()

    def die(self):
        self.is_alive = False
        self.energy = 0

    def digest(self, matter: Matter) -> float:
        """Break down eaten matter via the organism's metabolism (a
        catalyzed reaction: digestive enzymes make otherwise costly bonds
        cheap to break) and return the net energy released."""
        result = Reactor.react(matter.molecules, catalyzed=True)
        return result.energy_delta