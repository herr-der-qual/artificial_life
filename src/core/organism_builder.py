import random

import pymunk

from ai.brain import Brain
from simulation.organism import Organism
from simulation.matter import Matter


class OrganismBuilder:
    def __init__(self):
        self.speed = 20
        self.energy = 100
        self.energy_drain_rate = 10
        self.color = (0, 255, 0)
        self.position = (0, 0)
        self.matter = None

    def set_position(self, position):
        self.position = position
        return self

    def set_speed(self, speed: float):
        self.speed = speed
        return self

    def set_energy(self, energy: float):
        self.energy = energy
        return self

    def set_energy_drain_rate(self, rate: float):
        self.energy_drain_rate = rate
        return self

    def set_color(self, color: tuple):
        self.color = color
        return self

    def set_matter(self, matter: Matter):
        self.matter = matter
        return self

    def build(self) -> 'Organism':
        organism = Organism(
            matter=self.matter,
            speed=self.speed,
            energy=self.energy,
            color=self.color,
        )
        organism.position = self.position
        organism.energy_drain_rate = self.energy_drain_rate

        return organism

