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

# Individual atoms within one molecule/cell pack tighter than whole cells do
# - kept small enough that a molecule's atoms stay roughly within the same
# footprint as CELL_TRIANGLE, so the atom-level render (Renderer) doesn't
# visibly outgrow the coarser physics hull (body_hull) it's drawn on top of.
ATOM_SPACING = 1.3
# Bigger than a tight packing radius (overlapping neighbors) - at typical
# zoomed-out camera distances a few world units is only a handful of
# screen pixels, and tiny sparse dots read as noise rather than a body.
ATOM_RADIUS = 1.6


def _spiral_offsets(count: int, spacing: float) -> list:
    if count <= 1:
        return [(0.0, 0.0)]

    offsets = []
    for i in range(count):
        r = spacing * math.sqrt(i)
        theta = i * GOLDEN_ANGLE
        offsets.append((r * math.cos(theta), r * math.sin(theta)))
    return offsets


def cell_offsets(count: int) -> list:
    return _spiral_offsets(count, CELL_SPACING)


def atom_positions(molecules: list) -> list:
    """Every atom's body-local (x, y, element) - cells (molecules) laid out
    via cell_offsets, each molecule's own atoms nested inside via a
    tighter spiral. Single source of truth for the atom-level render (see
    ui.renderer) - body_hull stays the coarser per-cell shape physics
    actually collides with."""
    molecules = list(molecules)
    positions = []
    for (cx, cy), molecule in zip(cell_offsets(max(1, len(molecules))), molecules):
        atom_offsets = _spiral_offsets(len(molecule.atoms), ATOM_SPACING)
        for (ax, ay), atom in zip(atom_offsets, molecule.atoms):
            positions.append((cx + ax, cy + ay, atom.element))
    return positions


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
