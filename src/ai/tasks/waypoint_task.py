import pymunk

from .task import Task


class WaypointTask(Task):
    def __init__(self, waypoint, organism):
        self.waypoint = pymunk.Vec2d(*waypoint)
        self.threshold = 5.0
        self.organism = organism

    def do(self):
        distance = self.waypoint - self.organism.position
        distance_length = distance.length

        if distance_length < self.threshold:
            self.organism.velocity = pymunk.Vec2d(0, 0)
            return True

        if distance_length > 0:
            norm_dir = distance.normalized()
            self.organism.velocity = norm_dir * self.organism.speed
        else:
            self.organism.velocity = pymunk.Vec2d(0, 0)

        return False