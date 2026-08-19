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
        nearest = None
        min_distance = float('inf')

        for other in self.world.organisms:
            if other is self.organism or not other.can_reproduce():
                continue

            distance = (other.position - self.organism.position).length
            if distance < self.organism.search_radius and distance < min_distance:
                min_distance = distance
                nearest = other

        return nearest

    def do(self):
        if self.target_mate is None or self.target_mate not in self.world.organisms \
                or not self.target_mate.can_reproduce():
            self.target_mate = self.find_nearest_mate()

        if self.target_mate is None:
            self.organism.velocity = pymunk.Vec2d(0, 0)
            return True

        distance = self.target_mate.position - self.organism.position
        distance_length = distance.length

        if distance_length < 10:
            if distance_length > 0:
                norm_dir = distance.normalized()
                self.organism.velocity = norm_dir * (self.organism.speed * 0.5)
            return False

        norm_dir = distance.normalized()
        self.organism.velocity = norm_dir * self.organism.speed

        return False
