from src_grid.simulation.grid import Grid
from src_grid.core.organism_factory import OrganismFactory


def test_step_moves_to_an_adjacent_cell_or_stays_put():
    grid = Grid(10, 10)
    organism = OrganismFactory.create_random()
    grid.place(organism, 5, 5)

    organism.step(grid)

    col, row = organism.position
    distance = abs(col - 5) + abs(row - 5)
    assert distance in (0, 1)  # 0 if the random direction happened to be blocked (edge case, not here)


def test_step_never_moves_onto_an_occupied_cell():
    grid = Grid(3, 3)
    mover = OrganismFactory.create_random()
    grid.place(mover, 1, 1)

    # surround the mover on all 4 sides so every possible step is blocked
    blockers = [OrganismFactory.create_random() for _ in range(4)]
    for blocker, (col, row) in zip(blockers, [(2, 1), (0, 1), (1, 2), (1, 0)]):
        grid.place(blocker, col, row)

    for _ in range(20):
        mover.step(grid)

    assert mover.position == (1, 1)
    for blocker, expected in zip(blockers, [(2, 1), (0, 1), (1, 2), (1, 0)]):
        assert blocker.position == expected
