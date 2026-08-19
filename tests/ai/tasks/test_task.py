import pytest

from ai.tasks.task import seek_velocity


def test_seek_velocity_moves_at_full_speed_when_far_from_target():
    dx, dy = 100.0, 0.0
    vx, vy = seek_velocity(dx, dy, distance_length=100.0, speed=30.0, physics_dt=1 / 60)
    assert vx == pytest.approx(30.0)
    assert vy == pytest.approx(0.0)


def test_seek_velocity_clamps_to_avoid_overshoot_at_large_physics_dt():
    """Regression target: at a large physics_dt (fast simulation speeds),
    an organism close to its target used to get sent flying straight past
    it in one tick, then yanked back the other way next tick - jittering
    in place instead of arriving. The clamped velocity must land exactly
    on the target this tick, not further."""
    distance_length = 5.0
    physics_dt = 1.0  # deliberately huge, e.g. the "MAX" speed multiplier
    speed = 30.0  # speed * physics_dt (30) would fly way past a 5-unit gap

    vx, vy = seek_velocity(distance_length, 0.0, distance_length, speed, physics_dt)

    displacement = vx * physics_dt
    assert displacement == pytest.approx(distance_length)
    assert displacement <= distance_length + 1e-9


def test_seek_velocity_does_not_clamp_when_target_is_far_relative_to_physics_dt():
    dx, dy = 1000.0, 0.0
    physics_dt = 1.0
    speed = 30.0

    vx, vy = seek_velocity(dx, dy, 1000.0, speed, physics_dt)

    assert vx == pytest.approx(speed)  # unclamped - nowhere near reaching it this tick


def test_seek_velocity_is_zero_at_zero_distance():
    assert seek_velocity(0.0, 0.0, 0.0, 30.0, 1 / 60) == (0.0, 0.0)


def test_seek_velocity_is_zero_when_physics_dt_is_zero():
    """Paused/zero-dt ticks must not divide by zero."""
    assert seek_velocity(10.0, 0.0, 10.0, 30.0, 0.0) == (0.0, 0.0)
