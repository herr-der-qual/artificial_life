import math

import pytest

from core.speed_scale import (
    slider_to_fps, fps_to_slider, format_fps, fps_to_physics_multiplier,
    MIN_FPS, MAX_FINITE_FPS, MIN_PHYSICS_MULTIPLIER, MAX_PHYSICS_MULTIPLIER, INFINITE_PHYSICS_MULTIPLIER,
)


def test_min_slider_gives_min_fps():
    assert slider_to_fps(0.0) == pytest.approx(MIN_FPS)


def test_top_of_slider_is_infinite():
    assert slider_to_fps(1.0) == math.inf


def test_slider_is_monotonic_below_infinite_zone():
    values = [slider_to_fps(t) for t in (0.0, 0.2, 0.4, 0.6, 0.8, 0.94)]
    assert values == sorted(values)


def test_finite_fps_stays_within_bounds():
    for t in (0.0, 0.25, 0.5, 0.75, 0.9):
        fps = slider_to_fps(t)
        assert MIN_FPS <= fps <= MAX_FINITE_FPS


@pytest.mark.parametrize("fps", [1.0, 5.0, 60.0, 500.0, 1000.0])
def test_fps_to_slider_round_trips(fps):
    t = fps_to_slider(fps)
    assert slider_to_fps(t) == pytest.approx(fps, rel=1e-6)


def test_infinite_round_trips():
    assert fps_to_slider(math.inf) == 1.0
    assert slider_to_fps(fps_to_slider(math.inf)) == math.inf


def test_out_of_range_slider_values_are_clamped():
    assert slider_to_fps(-1.0) == slider_to_fps(0.0)
    assert slider_to_fps(2.0) == math.inf


def test_format_fps():
    assert format_fps(60.0) == "60"
    assert format_fps(math.inf) == "MAX"


def test_min_fps_gives_min_physics_multiplier():
    assert fps_to_physics_multiplier(MIN_FPS) == pytest.approx(MIN_PHYSICS_MULTIPLIER)


def test_max_finite_fps_gives_max_physics_multiplier():
    assert fps_to_physics_multiplier(MAX_FINITE_FPS) == pytest.approx(MAX_PHYSICS_MULTIPLIER)


def test_infinite_fps_gets_its_own_dedicated_multiplier():
    """MAX should feel qualitatively faster than just "a high finite
    number", not merely the log curve's endpoint."""
    assert fps_to_physics_multiplier(math.inf) == pytest.approx(INFINITE_PHYSICS_MULTIPLIER)
    assert INFINITE_PHYSICS_MULTIPLIER > MAX_PHYSICS_MULTIPLIER


def test_physics_multiplier_is_monotonic_across_finite_fps():
    values = [fps_to_physics_multiplier(fps) for fps in (1.0, 5.0, 60.0, 500.0, 1000.0)]
    assert values == sorted(values)
