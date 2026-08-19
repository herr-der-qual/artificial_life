import math

MIN_FPS = 1.0
MAX_FINITE_FPS = 1000.0

# The top slice of the slider is a dedicated "infinite" zone - past this
# point the simulation runs uncapped, using as much CPU as it can.
INFINITE_ZONE_START = 0.95


def slider_to_fps(t: float) -> float:
    """Map a slider position in [0, 1] to a target FPS.

    Log scale between MIN_FPS and MAX_FINITE_FPS gives fine control at the
    slow end (where the difference between 1 and 5 FPS matters a lot) while
    still reaching a fast finite rate before snapping to unlimited.
    """
    t = max(0.0, min(1.0, t))

    if t > INFINITE_ZONE_START:
        return math.inf

    u = t / INFINITE_ZONE_START
    return MIN_FPS * (MAX_FINITE_FPS / MIN_FPS) ** u


def fps_to_slider(fps) -> float:
    if fps == math.inf:
        return 1.0

    fps = max(MIN_FPS, min(float(fps), MAX_FINITE_FPS))
    u = math.log(fps / MIN_FPS) / math.log(MAX_FINITE_FPS / MIN_FPS)
    return u * INFINITE_ZONE_START


def format_fps(fps) -> str:
    if fps == math.inf:
        return "MAX"
    return f"{fps:.0f}"


# Movement is deliberately faster than the metabolism clock (see World.
# fixed_update) so it's watchable at all - but a flat multiplier makes the
# speed slider only change how OFTEN a tick happens, not how big each one
# looks, so slow and fast settings can end up feeling similar. Scaling the
# multiplier with the slider too makes the low end feel deliberate and the
# high end feel dramatically faster, on top of the extra ticks/sec.
MIN_PHYSICS_MULTIPLIER = 3.0
MAX_PHYSICS_MULTIPLIER = 20.0
INFINITE_PHYSICS_MULTIPLIER = 40.0


def fps_to_physics_multiplier(fps) -> float:
    """Log-scale, matching slider_to_fps's own curve - the "MAX" end of the
    slider gets an extra jump on top of the curve, so it reads as
    qualitatively different from just "a high finite number"."""
    if fps == math.inf:
        return INFINITE_PHYSICS_MULTIPLIER

    fps = max(MIN_FPS, min(float(fps), MAX_FINITE_FPS))
    u = math.log(fps / MIN_FPS) / math.log(MAX_FINITE_FPS / MIN_FPS)
    return MIN_PHYSICS_MULTIPLIER * (MAX_PHYSICS_MULTIPLIER / MIN_PHYSICS_MULTIPLIER) ** u
