from abc import ABC, abstractmethod


class Goal(ABC):
    """A prioritized behavior an organism can pursue. Brain checks goals in
    order and switches to the first one that's active, unless it's already
    the one being pursued."""

    task_class = None

    @abstractmethod
    def is_active(self, organism, world) -> bool:
        """Whether this goal should take over right now."""

    @abstractmethod
    def create_task(self, organism, world):
        """Build the task that pursues this goal."""

    def matches_current(self, task) -> bool:
        return isinstance(task, self.task_class)
