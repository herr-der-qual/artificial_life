import pytest

from ai.tasks.waypoint_task import WaypointTask


class FakeWorld:
    def __init__(self, physics_dt):
        self.physics_dt = physics_dt


class FakeBrain:
    def __init__(self, world):
        self.world = world


class FakeOrganism:
    def __init__(self, position, speed, physics_dt):
        self.position = position
        self.speed = speed
        self.velocity = (0.0, 0.0)
        self.brain = FakeBrain(FakeWorld(physics_dt))


def test_waypoint_task_does_not_overshoot_at_a_large_physics_dt():
    """Regression target: at fast simulation speeds (large physics_dt), an
    organism close to its waypoint used to fly straight past it in one
    tick and get yanked back the next - jittering in place rather than
    arriving. One tick's displacement must never exceed the remaining
    distance to the waypoint."""
    organism = FakeOrganism(position=type("P", (), {"x": 0.0, "y": 0.0})(), speed=30.0, physics_dt=1.0)
    task = WaypointTask((5.0, 0.0), organism)

    task.do()

    vx, vy = organism.velocity
    displacement = vx * organism.brain.world.physics_dt
    assert displacement == pytest.approx(5.0)
    assert displacement <= 5.0 + 1e-9


def test_waypoint_task_moves_at_full_speed_when_far_relative_to_physics_dt():
    organism = FakeOrganism(position=type("P", (), {"x": 0.0, "y": 0.0})(), speed=30.0, physics_dt=1 / 60)
    task = WaypointTask((1000.0, 0.0), organism)

    task.do()

    vx, vy = organism.velocity
    assert vx == pytest.approx(30.0)
