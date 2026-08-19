import pymunk
from .task import Task


class SeekFoodTask(Task):
    """Task for seeking and moving towards the nearest food substance"""

    def __init__(self, organism, world):
        self.organism = organism
        self.world = world
        self.target_food = None

    def find_nearest_food(self):
        """Find the nearest substance within search radius.

        Uses the space's own spatial index (space.point_query) instead of
        scanning every substance in Python - with hundreds of organisms all
        hungry at once, a per-organism O(n) scan over every substance
        multiplies into millions of distance checks a second.
        """
        diet = self.organism.diet
        results = self.world.space.point_query(
            self.organism.position, self.organism.search_radius, pymunk.ShapeFilter(),
        )

        nearest = None
        min_distance = float('inf')

        for info in results:
            shape = info.shape
            if shape.collision_type != 1:
                continue

            substance = shape.body
            if substance.kind not in diet:
                continue

            if info.distance < min_distance:
                min_distance = info.distance
                nearest = substance

        return nearest

    def do(self):
        """Execute the task: seek and move towards nearest food"""
        if not self.world.substances:
            self.organism.velocity = pymunk.Vec2d(0, 0)
            return True

        # Find or update target
        if self.target_food is None or self.target_food.removed:
            self.target_food = self.find_nearest_food()

        # No food found within range
        if self.target_food is None:
            self.organism.velocity = pymunk.Vec2d(0, 0)
            return True

        distance = self.target_food.position - self.organism.position
        distance_length = distance.length

        if distance_length < 10:
            if distance_length > 0:
                norm_dir = distance.normalized()
                self.organism.velocity = norm_dir * (self.organism.speed * 0.5)
            return False

        # Move towards food at full speed
        if distance_length > 0:
            norm_dir = distance.normalized()
            self.organism.velocity = norm_dir * self.organism.speed
        else:
            self.organism.velocity = pymunk.Vec2d(0, 0)

        return False  # Task not complete, keep seeking
