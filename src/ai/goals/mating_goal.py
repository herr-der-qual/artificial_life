from .goal import Goal
from ai.tasks.seek_mate_task import SeekMateTask


class MatingGoal(Goal):
    task_class = SeekMateTask

    def is_active(self, organism, world) -> bool:
        if not world or not world.organisms:
            return False

        return organism.can_reproduce()

    def create_task(self, organism, world):
        return SeekMateTask(organism, world)
