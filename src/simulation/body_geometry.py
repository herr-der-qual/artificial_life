import math

# Sunflower-seed spiral: deterministic, organic-looking packing so a
# multicellular body's cells spread outward instead of stacking on top of
# each other.
GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))

# Matches the single-cell triangle silhouette this project has always used -
# a multicellular body is built from copies of the same triangle, not a
# different base shape, so a cell_count of 1 renders/collides pixel-for-
# pixel identical to what it always was.
CELL_TRIANGLE = ((-4.0, -4.0), (0.0, 4.0), (4.0, -4.0))
CELL_SPACING = 4.0  # world units between successive cells in the spiral


def cell_offsets(count: int) -> list:
    if count <= 1:
        return [(0.0, 0.0)]

    offsets = []
    for i in range(count):
        r = CELL_SPACING * math.sqrt(i)
        theta = i * GOLDEN_ANGLE
        offsets.append((r * math.cos(theta), r * math.sin(theta)))
    return offsets


def _convex_hull(points: list) -> list:
    """Andrew's monotone chain. Returns hull vertices in CCW order."""
    points = sorted(set(points))
    if len(points) <= 2:
        return points

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def body_hull(cell_count: int, scale: float = 1.0) -> list:
    """Convex hull of `cell_count` copies of the cell triangle, arranged in
    a spiral and scaled - the single source of truth for what an N-cell
    body looks like. Used both for the physics shape (Substance) and the
    render texture (Renderer), so what's drawn always matches what's
    actually collided with."""
    cell_count = max(1, cell_count)

    points = []
    for ox, oy in cell_offsets(cell_count):
        for vx, vy in CELL_TRIANGLE:
            points.append((ox + vx, oy + vy))

    hull = _convex_hull(points)
    return [(x * scale, y * scale) for x, y in hull]
