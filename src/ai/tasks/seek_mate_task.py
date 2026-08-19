import math

import pymunk
from .task import Task


class SeekMateTask(Task):
    """Move towards the nearest fertile organism. Mating itself happens via
    the organism-organism collision handler in World, same split as
    SeekFoodTask (seek) / World.on_organism_eat_substance (eat)."""

    def __init__(self, organism, world):
        self.organism = organism
        self.world = world
        self.target_mate = None

    def find_nearest_mate(self):
        """Uses the space's spatial index instead of scanning every
        organism in Python - see SeekFoodTask.find_nearest_food."""
        results = self.world.space.point_query(
            self.organism.position, self.organism.search_radius, pymunk.ShapeFilter(),
        )

        nearest = None
        min_distance = float('inf')

        for info in results:
            shape = info.shape
            if shape.collision_type != 2:
                continue

            other = shape.body
            if other is self.organism or not other.can_reproduce():
                continue

            if info.distance < min_distance:
                min_distance = info.distance
                nearest = other

        return nearest

    def do(self):
        if self.target_mate is None or self.target_mate.removed or not self.target_mate.can_reproduce():
            self.target_mate = self.find_nearest_mate()

        if self.target_mate is None:
            self.organism.velocity = (0.0, 0.0)
            return True

        # Plain-float math instead of pymunk.Vec2d arithmetic - Vec2d's
        # operators assert isinstance(other, numbers.Real) on every call,
        # and numbers.Real is an ABC, so at thousands of organisms/tick
        # this alone dominated profiled step time (see perf notes).
        mate_position = self.target_mate.position
        position = self.organism.position
        dx = mate_position.x - position.x
        dy = mate_position.y - position.y
        distance_length = math.hypot(dx, dy)

        if distance_length < 10:
            if distance_length > 0:
                scale = (self.organism.speed * 0.5) / distance_length
                self.organism.velocity = (dx * scale, dy * scale)
            return False

        scale = self.organism.speed / distance_length
        self.organism.velocity = (dx * scale, dy * scale)

        return False
