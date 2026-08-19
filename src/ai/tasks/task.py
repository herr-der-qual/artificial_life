from abc import ABC, abstractmethod


class Task(ABC):
    @abstractmethod
    def do(self, *args, **kwargs) -> bool:
        pass


def seek_velocity(dx: float, dy: float, distance_length: float, speed: float, physics_dt: float) -> tuple:
    """Velocity to close a (dx, dy) gap this tick without overshooting past
    the target. Unclamped, `speed` alone can carry an organism past a near
    target in a single tick once physics_dt gets large (fast simulation
    speeds) - next tick's task then aims it back the other way, overshoots
    again, and it oscillates in place instead of arriving."""
    if distance_length <= 0 or physics_dt <= 0:
        return 0.0, 0.0

    effective_speed = min(speed, distance_length / physics_dt)
    scale = effective_speed / distance_length
    return dx * scale, dy * scale
