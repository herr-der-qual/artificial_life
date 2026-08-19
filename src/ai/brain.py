import random

from ai.tasks.task import Task
from ai.tasks.waypoint_task import WaypointTask
from ai.goals import HungerGoal, MatingGoal


class Brain:
    def __init__(self, organism):
        self.organism = organism
        self.tasks: list[Task] = []
        self.world = None

        # Priority order: survival goals before anything else.
        self.goals = [
            HungerGoal(),
            MatingGoal(),
        ]

    def add_task(self, task: Task):
        self.tasks.append(task)

    def update(self):
        active_goal = self._active_goal()

        if active_goal is not None:
            already_pursuing = self.tasks and active_goal.matches_current(self.tasks[0])
            if not already_pursuing:
                self.tasks.clear()
                self.add_task(active_goal.create_task(self.organism, self.world))

        if not self.tasks:
            self.generate_task()
            return

        current_task = self.tasks[0]
        if current_task.do():
            self.tasks.pop(0)

    def _active_goal(self):
        for goal in self.goals:
            if goal.is_active(self.organism, self.world):
                return goal
        return None

    def generate_task(self):
        min_radius = 5
        radius = max(min_radius, self.organism.wander_radius)
        x = random.uniform(min_radius, radius)
        x = self.organism.position.x + x * random.choice((1, -1))

        y = random.uniform(min_radius, radius)
        y = self.organism.position.y + y * random.choice((1, -1))

        self.add_task(WaypointTask((x, y), self.organism))
