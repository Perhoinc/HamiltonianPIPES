"""Unified counting interface: picks the fastest orientation and dispatches
to the profile DP (hamiltonian.profile_dp), and offers a convenience
wrapper around the brute-force example-path finder."""

from __future__ import annotations

from typing import Optional

from .brute_force import find_one_hamiltonian_cycle, find_one_hamiltonian_path
from .grid import Cell, Grid
from .profile_dp import count_structures


def _best_orientation(grid: Grid) -> Grid:
    """The profile DP's state space grows with the number of columns, so
    orient the grid so the smaller dimension is the column count."""
    return grid.transposed() if grid.cols > grid.rows else grid


def count_paths(grid: Grid) -> int:
    """Exact count of undirected Hamiltonian paths covering every open cell."""
    return count_structures(_best_orientation(grid), "path")


def count_cycles(grid: Grid) -> int:
    """Exact count of undirected Hamiltonian cycles covering every open cell."""
    return count_structures(_best_orientation(grid), "cycle")


def example_path(grid: Grid, seed: Optional[int] = None) -> Optional[list[Cell]]:
    """Find one example Hamiltonian path (list of cells in visiting order),
    or None if none exists."""
    return find_one_hamiltonian_path(grid, seed=seed)


def example_cycle(grid: Grid, seed: Optional[int] = None) -> Optional[list[Cell]]:
    """Find one example Hamiltonian cycle (list of cells in visiting order,
    with the last cell adjacent back to the first), or None if none exists."""
    return find_one_hamiltonian_cycle(grid, seed=seed)
