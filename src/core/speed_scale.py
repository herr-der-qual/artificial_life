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
