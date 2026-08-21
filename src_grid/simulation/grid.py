class Grid:
    """A discrete 2D field of cells. Each cell holds at most one occupant -
    the whole point of the discrete model: two things simply can't share a
    cell, so there's no continuous-position overlap math needed at all.

    Also maintains a spatial index: occupied positions bucketed into
    BUCKET_SIZE x BUCKET_SIZE regions, kept in sync inside place()/
    remove()/move() (the only three ways _cells ever changes) so it can
    never drift out of sync with the cells themselves. nearby_positions()
    uses it to answer "what's near (col, row)" by checking a handful of
    buckets instead of scanning every cell in the search area - see
    Organism._nearest_visible_food, which used to scan the full square
    even when almost every cell in it was empty (profiled as the single
    biggest cost in World.update() at a few thousand organisms)."""

    # Empirically tuned (see git history) against Organism.SEARCH_RADIUS=5
    # on a realistic sparse world - too big and each bucket overshoots the
    # actual search radius by a lot (more positions to filter back out
    # than a raw scan would've checked in the first place); too small and
    # per-bucket dict-lookup overhead dominates instead. 2-4 was the flat
    # bottom of that curve; this isn't a hard rule for every radius/
    # density combination, just what measured best for the one we have.
    BUCKET_SIZE = 3

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._cells = {}  # (col, row) -> occupant
        self._buckets = {}  # (bucket_col, bucket_row) -> set of occupied (col, row)

    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.width and 0 <= row < self.height

    def is_free(self, col: int, row: int) -> bool:
        return self.in_bounds(col, row) and (col, row) not in self._cells

    def occupant_at(self, col: int, row: int):
        return self._cells.get((col, row))

    def place(self, entity, col: int, row: int):
        if not self.is_free(col, row):
            raise ValueError(f"Cell ({col}, {row}) is occupied or out of bounds")

        self._cells[(col, row)] = entity
        entity.position = (col, row)
        self._bucket_for(col, row).add((col, row))

    def remove(self, entity):
        col, row = entity.position
        del self._cells[(col, row)]
        self._discard_from_bucket(col, row)

    def move(self, entity, col: int, row: int) -> bool:
        """Move `entity` to (col, row) if that cell is free. Returns
        whether the move happened - callers decide what a blocked move
        means (stay put, try another direction, etc.), this just enforces
        that two entities never occupy the same cell."""
        if not self.is_free(col, row):
            return False

        old_col, old_row = entity.position
        del self._cells[(old_col, old_row)]
        self._discard_from_bucket(old_col, old_row)

        self._cells[(col, row)] = entity
        entity.position = (col, row)
        self._bucket_for(col, row).add((col, row))
        return True

    def nearby_positions(self, col: int, row: int, radius: int):
        """Occupied positions within `radius` cells (Chebyshev distance -
        a square, not a diamond) of (col, row), including (col, row)
        itself if occupied. Only visits buckets that could possibly hold
        a match, not every cell in the square - callers still need to
        filter by distance/type themselves (this doesn't know what a
        Food or Organism is)."""
        bucket_col, bucket_row = self._bucket_coords(col, row)
        bucket_span = radius // self.BUCKET_SIZE + 1

        for bc in range(bucket_col - bucket_span, bucket_col + bucket_span + 1):
            for br in range(bucket_row - bucket_span, bucket_row + bucket_span + 1):
                bucket = self._buckets.get((bc, br))
                if not bucket:
                    continue
                for pos in bucket:
                    pcol, prow = pos
                    if abs(pcol - col) <= radius and abs(prow - row) <= radius:
                        yield pos

    def _bucket_coords(self, col: int, row: int) -> tuple:
        return col // self.BUCKET_SIZE, row // self.BUCKET_SIZE

    def _bucket_for(self, col: int, row: int) -> set:
        return self._buckets.setdefault(self._bucket_coords(col, row), set())

    def _discard_from_bucket(self, col: int, row: int):
        key = self._bucket_coords(col, row)
        bucket = self._buckets[key]
        bucket.discard((col, row))
        if not bucket:
            del self._buckets[key]

    def __iter__(self):
        return iter(self._cells.values())

    def __len__(self):
        return len(self._cells)
