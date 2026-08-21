class Grid:
    """A discrete 2D field of cells. Each cell holds at most one occupant -
    the whole point of the discrete model: two things simply can't share a
    cell, so there's no continuous-position overlap math needed at all."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._cells = {}  # (col, row) -> occupant

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

    def remove(self, entity):
        del self._cells[entity.position]

    def move(self, entity, col: int, row: int) -> bool:
        """Move `entity` to (col, row) if that cell is free. Returns
        whether the move happened - callers decide what a blocked move
        means (stay put, try another direction, etc.), this just enforces
        that two entities never occupy the same cell."""
        if not self.is_free(col, row):
            return False

        del self._cells[entity.position]
        self._cells[(col, row)] = entity
        entity.position = (col, row)
        return True

    def __iter__(self):
        return iter(self._cells.values())

    def __len__(self):
        return len(self._cells)
