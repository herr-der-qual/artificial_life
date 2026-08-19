import math

from .task import Task, seek_velocity


class WaypointTask(Task):
    def __init__(self, waypoint, organism):
        self.waypoint = waypoint
        self.threshold = 5.0
        self.organism = organism

    def do(self):
        # Plain-float math instead of pymunk.Vec2d arithmetic - Vec2d's
        # operators assert isinstance(other, numbers.Real) on every call,
        # and numbers.Real is an ABC, so at thousands of organisms/tick
        # this alone dominated profiled step time (see perf notes).
        position = self.organism.position
        dx = self.waypoint[0] - position.x
        dy = self.waypoint[1] - position.y
        distance_length = math.hypot(dx, dy)

        if distance_length < self.threshold:
            self.organism.velocity = (0.0, 0.0)
            return True

        world = self.organism.brain.world
        physics_dt = world.physics_dt if world else 1 / 60
        self.organism.velocity = seek_velocity(dx, dy, distance_length, self.organism.speed, physics_dt)

        return False
