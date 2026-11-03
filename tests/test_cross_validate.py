"""Cross-validate the polynomial profile DP against exhaustive brute-force
enumeration on small grids -- rectangular, non-rectangular (holes), and
degenerate shapes. If these agree across a good variety of shapes, we trust
the DP on the larger grids brute force can't handle."""

import pytest

from hamiltonian.brute_force import count_cycles_bruteforce, count_paths_bruteforce
from hamiltonian.counting import count_cycles, count_paths
from hamiltonian.grid import Grid


def rectangular_grids():
    for rows in range(1, 5):
        for cols in range(1, 5):
            if rows * cols <= 16:
                yield Grid.full(rows, cols)


def holey_grids():
    shapes = [
        (3, 3, [(1, 1)]),
        (3, 3, [(0, 0)]),
        (4, 4, [(1, 1), (2, 2)]),
        (4, 4, [(0, 1), (1, 1), (2, 1)]),
        (3, 4, [(1, 1), (1, 2)]),
        (4, 3, [(0, 0), (3, 2)]),
        (5, 3, [(2, 1)]),
        (3, 5, [(1, 2), (0, 2)]),
        (4, 4, [(0, 0), (0, 3), (3, 0), (3, 3)]),  # corners removed
        (5, 5, [(2, 0), (2, 1), (2, 3), (2, 4)]),  # near-split
        (3, 3, [(2, 1), (2, 2)]),  # regression: dangling plug into a
        # trailing blocked cell was once miscounted as a solved path
    ]
    for rows, cols, blocked in shapes:
        yield Grid.from_blocked(rows, cols, blocked)


def all_test_grids():
    return list(rectangular_grids()) + list(holey_grids())


@pytest.mark.parametrize("grid", all_test_grids(), ids=lambda g: f"{g.rows}x{g.cols}_b{len(g.blocked)}")
def test_path_count_matches_bruteforce(grid):
    expected = count_paths_bruteforce(grid)
    actual = count_paths(grid)
    assert actual == expected, f"path count mismatch for\n{grid}\nexpected={expected} actual={actual}"


@pytest.mark.parametrize("grid", all_test_grids(), ids=lambda g: f"{g.rows}x{g.cols}_b{len(g.blocked)}")
def test_cycle_count_matches_bruteforce(grid):
    expected = count_cycles_bruteforce(grid)
    actual = count_cycles(grid)
    assert actual == expected, f"cycle count mismatch for\n{grid}\nexpected={expected} actual={actual}"


def test_single_cell():
    g = Grid.full(1, 1)
    assert count_paths(g) == 1
    assert count_cycles(g) == 0


def test_disconnected_grid_gives_zero():
    # Two separate 1x2 dominoes, no way to visit both in one path/cycle.
    g = Grid.from_blocked(1, 5, [(0, 2)])
    assert count_paths(g) == 0
    assert count_cycles(g) == 0


def test_line_grid_has_no_cycle():
    g = Grid.full(1, 6)
    assert count_paths(g) == 1
    assert count_cycles(g) == 0


def test_known_small_values():
    # 2x2 is a 4-cycle graph: every Hamiltonian path is that cycle minus
    # one edge (4 ways), and there's exactly 1 Hamiltonian cycle.
    assert count_paths(Grid.full(2, 2)) == 4
    assert count_cycles(Grid.full(2, 2)) == 1
