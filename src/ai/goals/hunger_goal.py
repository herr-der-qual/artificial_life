from .goal import Goal
from ai.tasks.seek_food_task import SeekFoodTask


class HungerGoal(Goal):
    task_class = SeekFoodTask
    threshold = 0.4

    def is_active(self, organism, world) -> bool:
        if not world or not world.substances:
            return False

        return organism.energy / organism.max_energy < self.threshold

    def create_task(self, organism, world):
        return SeekFoodTask(organism, world)
