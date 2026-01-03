import random

from ai.tasks import *
from ai.tasks.seek_food_task import SeekFoodTask


class Brain:
    def __init__(self, organism):
        self.organism = organism
        self.tasks: list[Task] = []
        self.world = None
        self.hunger_threshold = 0.4

    def add_task(self, task: Task):
        self.tasks.append(task)

    def update(self):
        if self.should_seek_food():
            self.tasks.clear()
            self.add_task(SeekFoodTask(self.organism, self.world))

        if not self.tasks:
            self.generate_task()
            return

        current_task = self.tasks[0]
        if current_task.do():
            self.tasks.pop(0)

    def should_seek_food(self):
        if not self.world or not self.world.substances:
            return False

        # Already seeking food
        if self.tasks and isinstance(self.tasks[0], SeekFoodTask):
            return False

        # Check if energy is below hunger threshold
        energy_ratio = self.organism.energy / self.organism.max_energy
        return energy_ratio < self.hunger_threshold

    def generate_task(self):
        min_radius = 5
        radius = 30
        x = random.uniform(min_radius, radius)
        x = self.organism.position.x + x * random.choice((1, -1))

        y = random.uniform(min_radius, radius)
        y = self.organism.position.y + y * random.choice((1, -1))

        self.add_task(WaypointTask((x, y), self.organism))
