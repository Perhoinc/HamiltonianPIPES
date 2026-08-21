"""Exact brute-force enumeration.

Used for two purposes:
  1. Ground truth to cross-validate the polynomial-time profile DP counter
     (see profile_dp.py) on small grids.
  2. Fast single-solution search (with pruning heuristics) to find an example
     path/cycle to visualize, which works even on grids too large to count
     exhaustively.

Counting conventions: a Hamiltonian path/cycle is counted as an *undirected*
edge set -- i.e. a route and its reverse traversal are the same path, and a
cycle doesn't care which cell you call the "start" or which direction you
walk it. This matches what profile_dp.py computes.
"""

from __future__ import annotations

import random
from typing import Optional

from .grid import Cell, Grid


def _index_cells(grid: Grid) -> tuple[list[Cell], dict[Cell, int]]:
    cells = list(grid.open_cells())
    index = {cell: i for i, cell in enumerate(cells)}
    return cells, index


def count_paths_bruteforce(grid: Grid) -> int:
    """Exact count of undirected Hamiltonian paths, via exhaustive DFS.

    Only tractable for small grids (a few dozen open cells at most) -- this
    exists as ground truth for tests, not as the production counting path.
    """
    n = grid.num_open
    if n == 0:
        return 0
    if n == 1:
        return 1

    cells, index = _index_cells(grid)
    neighbor_masks = _neighbor_masks(grid, cells, index)

    directed_total = 0

    def dfs(pos: int, visited: int, depth: int) -> None:
        nonlocal directed_total
        if depth == n:
            directed_total += 1
            return
        for nxt in _iter_set_bits(neighbor_masks[pos] & ~visited):
            dfs(nxt, visited | (1 << nxt), depth + 1)

    for start in range(n):
        dfs(start, 1 << start, 1)

    assert directed_total % 2 == 0
    return directed_total // 2


def count_cycles_bruteforce(grid: Grid) -> int:
    """Exact count of undirected Hamiltonian cycles, via exhaustive DFS."""
    n = grid.num_open
    if n < 4:
        # Simple grid graphs are bipartite: the shortest possible cycle has
        # length 4, so fewer than 4 open cells can never form one.
        return 0

    cells, index = _index_cells(grid)
    neighbor_masks = _neighbor_masks(grid, cells, index)

    start = 0
    directed_total = 0

    def dfs(pos: int, visited: int, depth: int) -> None:
        nonlocal directed_total
        if depth == n:
            if start in _iter_set_bits(neighbor_masks[pos]):
                directed_total += 1
            return
        for nxt in _iter_set_bits(neighbor_masks[pos] & ~visited):
            dfs(nxt, visited | (1 << nxt), depth + 1)

    dfs(start, 1 << start, 1)

    assert directed_total % 2 == 0
    return directed_total // 2


def _neighbor_masks(grid: Grid, cells: list[Cell], index: dict[Cell, int]) -> list[int]:
    masks = []
    for (r, c) in cells:
        m = 0
        for nb in grid.neighbors(r, c):
            m |= 1 << index[nb]
        masks.append(m)
    return masks


def _iter_set_bits(mask: int):
    while mask:
        low = mask & (-mask)
        idx = low.bit_length() - 1
        yield idx
        mask ^= low


def _remaining_is_connected(grid: Grid, cells: list[Cell], index: dict[Cell, int], visited: int, frm: int) -> bool:
    """Flood-fill prune: are all not-yet-visited open cells still reachable
    from `frm` through not-yet-visited cells? If not, no completion is
    possible from here."""
    n = len(cells)
    remaining = (~visited) & ((1 << n) - 1)
    if remaining == 0:
        return True
    stack = [frm]
    seen = 1 << frm
    r, c = cells[frm]
    for nb in grid.neighbors(r, c):
        nb_idx = index[nb]
        if remaining & (1 << nb_idx):
            stack.append(nb_idx)
            seen |= 1 << nb_idx
    while stack:
        cur = stack.pop()
        cr, cc = cells[cur]
        for nb in grid.neighbors(cr, cc):
            nb_idx = index[nb]
            bit = 1 << nb_idx
            if (remaining & bit) and not (seen & bit):
                seen |= bit
                stack.append(nb_idx)
    return (seen & remaining) == remaining


def find_one_hamiltonian_path(grid: Grid, seed: Optional[int] = None) -> Optional[list[Cell]]:
    """Find a single Hamiltonian path via DFS with Warnsdorff ordering and
    connectivity pruning. Fast in practice up to 10x10. Returns a list of
    cells in visiting order, or None if no path exists."""
    return _search_one(grid, want_cycle=False, seed=seed)


def find_one_hamiltonian_cycle(grid: Grid, seed: Optional[int] = None) -> Optional[list[Cell]]:
    """Find a single Hamiltonian cycle via DFS with Warnsdorff ordering and
    connectivity pruning. Returns a list of cells in visiting order (first
    cell is adjacent to the last, closing the loop), or None if none exists."""
    return _search_one(grid, want_cycle=True, seed=seed)


def _search_one(grid: Grid, want_cycle: bool, seed: Optional[int]) -> Optional[list[Cell]]:
    n = grid.num_open
    if n == 0:
        return None
    if n == 1:
        cell = next(grid.open_cells())
        return None if want_cycle else [cell]
    if want_cycle and n < 4:
        return None

    cells, index = _index_cells(grid)
    neighbor_masks = _neighbor_masks(grid, cells, index)
    full_mask = (1 << n) - 1
    rng = random.Random(seed)

    start_candidates = list(range(n))
    rng.shuffle(start_candidates)

    for start in start_candidates:
        path = _dfs_warnsdorff(start, 1 << start, [start], n, neighbor_masks, cells, index, grid, want_cycle, rng)
        if path is not None:
            return [cells[i] for i in path]
        if not want_cycle:
            # For open paths any single successful start is enough; if it
            # failed, trying a different, cheaper start is still worthwhile,
            # but exhaustively trying all is fine given the search is fast.
            continue
    return None


def _dfs_warnsdorff(
    pos: int,
    visited: int,
    path: list[int],
    n: int,
    neighbor_masks: list[int],
    cells: list[Cell],
    index: dict[Cell, int],
    grid: Grid,
    want_cycle: bool,
    rng: random.Random,
) -> Optional[list[int]]:
    if len(path) == n:
        if not want_cycle:
            return path
        start = path[0]
        return path if (neighbor_masks[pos] & (1 << start)) else None

    candidates = list(_iter_set_bits(neighbor_masks[pos] & ~visited))
    if not candidates:
        return None

    # Warnsdorff's rule: try the neighbor with the fewest onward options
    # first (breaks ties randomly to explore varied example solutions).
    def onward_degree(idx: int) -> int:
        return bin(neighbor_masks[idx] & ~(visited | (1 << idx))).count("1")

    rng.shuffle(candidates)
    if want_cycle:
        # For closed tours, plain Warnsdorff tends to burn the start cell's
        # few neighbors too early and then can't get back to close the
        # loop. Standard fix: avoid stepping onto a neighbor of the start
        # cell until forced to (i.e. deprioritize, don't forbid).
        start = path[0]
        start_neighbor_mask = neighbor_masks[start]
        candidates.sort(key=lambda idx: (bool(start_neighbor_mask & (1 << idx)), onward_degree(idx)))
    else:
        candidates.sort(key=onward_degree)

    for nxt in candidates:
        new_visited = visited | (1 << nxt)
        if not _remaining_is_connected(grid, cells, index, new_visited, nxt):
            continue
        path.append(nxt)
        result = _dfs_warnsdorff(nxt, new_visited, path, n, neighbor_masks, cells, index, grid, want_cycle, rng)
        if result is not None:
            return result
        path.pop()
    return None
