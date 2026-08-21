"""Exact polynomial-time counting of Hamiltonian paths/cycles on a grid,
via "broken profile" (a.k.a. plug/connectivity) dynamic programming.

Why this exists: for anything beyond small grids, the *number* of
Hamiltonian paths/cycles is astronomically large (billions to trillions),
so no algorithm can enumerate them one at a time. This DP counts them
without ever constructing an individual solution, by sweeping the grid
cell by cell (row-major order) and tracking, along the "broken profile"
boundary between processed and unprocessed cells, which cells currently
have a dangling path/cycle edge ("plug") crossing that boundary, and which
other dangling plug each one is connected to (so we can detect -- and
forbid -- a sub-loop closing before every cell has been visited).

State per boundary position is one of:
    EMPTY  -- no plug crosses here
    OPEN   -- a plug that is one end of a still-open 2-ended chain
    CLOSE  -- the other kind of plug of a still-open 2-ended chain
              (OPEN/CLOSE is just a label pair per chain; which end is
              called which is arbitrary but must be applied consistently
              so that matching partners can be found by balanced-bracket
              scanning, the same way you'd match parentheses)
    LONE   -- a plug that is the sole remaining dangling end of a chain
              whose *other* end has already been fixed as a path endpoint
              (only used when counting open paths, never cycles, since a
              cycle has no endpoints)

This technique is the standard approach used to compute exact Hamiltonian
cycle/path counts on grids in sequences such as OEIS A003763 -- it's
sometimes called "plug DP" in competitive programming. Correctness here is
established empirically: see tests/test_cross_validate.py, which checks
this DP against exhaustive brute-force enumeration across many small grid
shapes (rectangular and with holes) for both paths and cycles.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .grid import Grid

EMPTY, OPEN, CLOSE, LONE = 0, 1, 2, 3

State = Tuple[Tuple[int, ...], int, int]  # (profile, left, endpoints_used)


def _rest_is_empty(combined: Tuple[int, ...], c: int) -> bool:
    """True iff every boundary position other than the current cell's own
    two (c and c+1) is EMPTY. A closure at the last open cell is only a
    genuine full solution if nothing else is left dangling elsewhere in the
    profile (e.g. a plug that would have had nowhere valid to go, such as
    one pointing at a blocked cell)."""
    return all(v == EMPTY for i, v in enumerate(combined) if i != c and i != c + 1)


def _find_partner(combined: List[int], pos: int) -> int:
    """Given a balanced-bracket-like sequence `combined` (ignoring EMPTY and
    LONE entries), find the index of the OPEN/CLOSE partner of combined[pos].
    """
    val = combined[pos]
    if val == OPEN:
        balance = 1
        for k in range(pos + 1, len(combined)):
            v = combined[k]
            if v == OPEN:
                balance += 1
            elif v == CLOSE:
                balance -= 1
                if balance == 0:
                    return k
        raise AssertionError("no matching CLOSE found for OPEN plug")
    elif val == CLOSE:
        balance = 1
        for k in range(pos - 1, -1, -1):
            v = combined[k]
            if v == CLOSE:
                balance += 1
            elif v == OPEN:
                balance -= 1
                if balance == 0:
                    return k
        raise AssertionError("no matching OPEN found for CLOSE plug")
    raise AssertionError(f"plug type {val} has no bracket partner")


def _transition(
    combined: Tuple[int, ...],
    c: int,
    has_right: bool,
    has_down: bool,
    is_blocked: bool,
    is_last: bool,
    allow_lone: bool,
    max_endpoints: int,
    ep: int,
):
    """Enumerate the possible ways to resolve cell at column `c`, given the
    combined boundary array (length C+1, with combined[c] = the cell's left
    input and combined[c+1] = the cell's up input).

    Yields tuples: ("cont", new_profile, new_left, new_ep) for a transition
    that keeps the sweep going, or ("sol",) for a transition that completes
    a full Hamiltonian structure right here (only possible at the last open
    cell).
    """
    left_in = combined[c]
    up_in = combined[c + 1]

    def build(nc: List[int], down_out: int, right_out: int):
        new_profile = tuple(nc[:c]) + (down_out,) + tuple(nc[c + 2 :])
        return new_profile, right_out

    if is_blocked:
        if left_in != 0 or up_in != 0:
            return
        new_profile, new_left = build(list(combined), EMPTY, EMPTY)
        yield ("cont", new_profile, new_left, ep)
        return

    if left_in == EMPTY and up_in == EMPTY:
        # Degree 2: start a brand new chain turning through this cell.
        # The down-plug ends up spatially left of the right-plug on the
        # next boundary line (see module docstring), so by the OPEN-before-
        # CLOSE convention: down=OPEN, right=CLOSE.
        if has_right and has_down:
            new_profile, new_left = build(list(combined), OPEN, CLOSE)
            yield ("cont", new_profile, new_left, ep)
        # Degree 1 (open-path mode only): start a new path endpoint here.
        if allow_lone and ep < max_endpoints:
            if has_right:
                new_profile, new_left = build(list(combined), EMPTY, LONE)
                yield ("cont", new_profile, new_left, ep + 1)
            if has_down:
                new_profile, new_left = build(list(combined), LONE, EMPTY)
                yield ("cont", new_profile, new_left, ep + 1)
        return

    if (left_in == EMPTY) != (up_in == EMPTY):
        # Exactly one incoming plug.
        x = left_in or up_in
        pos_x = c if left_in != EMPTY else c + 1
        if x in (OPEN, CLOSE):
            # Degree 2: pass the chain through (straight or turning).
            if has_down:
                new_profile, new_left = build(list(combined), x, EMPTY)
                yield ("cont", new_profile, new_left, ep)
            if has_right:
                new_profile, new_left = build(list(combined), EMPTY, x)
                yield ("cont", new_profile, new_left, ep)
            # Degree 1 (open-path mode only): terminate this chain's end
            # here; its other, still-live end (found via bracket matching)
            # becomes a LONE plug. Always legal (the chain isn't fully
            # closed -- it still has one live end elsewhere).
            if allow_lone and ep < max_endpoints:
                nc = list(combined)
                partner_pos = _find_partner(nc, pos_x)
                nc[partner_pos] = LONE
                new_profile, new_left = build(nc, EMPTY, EMPTY)
                yield ("cont", new_profile, new_left, ep + 1)
        else:  # x == LONE
            # Degree 2: extend a chain that already has one fixed endpoint.
            if has_down:
                new_profile, new_left = build(list(combined), LONE, EMPTY)
                yield ("cont", new_profile, new_left, ep)
            if has_right:
                new_profile, new_left = build(list(combined), EMPTY, LONE)
                yield ("cont", new_profile, new_left, ep)
            # Degree 1: terminate this chain's last live end -- the whole
            # chain is now fully closed (both ends fixed). That's only a
            # valid Hamiltonian path if it happens to cover every cell,
            # i.e. this is the very last open cell.
            if allow_lone and is_last and ep + 1 == max_endpoints and _rest_is_empty(combined, c):
                yield ("sol",)
        return

    # Both left_in and up_in are nonzero: this cell must have degree 2,
    # joining the two incoming plugs together (no room for further edges).
    if left_in == LONE and up_in == LONE:
        # Joining two chains that each have only one (already-fixed-end)
        # live plug fully closes both -- valid only as the final cell, and
        # only if nothing else is left dangling elsewhere.
        if is_last and _rest_is_empty(combined, c):
            yield ("sol",)
        return

    if left_in == LONE or up_in == LONE:
        # One chain has a fixed end (LONE), the other is still a live
        # 2-ended chain (OPEN/CLOSE) -- joining them is always legal (they
        # can never be the same chain, since a LONE plug's chain has only
        # one live end total). The OPEN/CLOSE chain's other end becomes the
        # new LONE end of the merged chain.
        paired_pos = c if left_in in (OPEN, CLOSE) else c + 1
        nc = list(combined)
        partner_pos = _find_partner(nc, paired_pos)
        nc[partner_pos] = LONE
        new_profile, new_left = build(nc, EMPTY, EMPTY)
        yield ("cont", new_profile, new_left, ep)
        return

    # Both incoming plugs are OPEN/CLOSE (still-live 2-ended chains).
    nc = list(combined)
    partner_of_left = _find_partner(nc, c)
    if partner_of_left == c + 1:
        # They're the two ends of the *same* chain: joining them closes a
        # loop. In cycle mode that's a valid solution, but only at the very
        # last cell (otherwise it's a premature sub-loop). In path mode a
        # closed loop is never valid, however many cells remain -- a
        # Hamiltonian path must never contain a cycle.
        if is_last and not allow_lone and _rest_is_empty(combined, c):
            yield ("sol",)
        return

    # Different chains: merge them into one. Their other two live ends
    # become each other's new partners.
    partner_of_up = _find_partner(nc, c + 1)
    p1, p2 = sorted((partner_of_left, partner_of_up))
    nc[p1] = OPEN
    nc[p2] = CLOSE
    new_profile, new_left = build(nc, EMPTY, EMPTY)
    yield ("cont", new_profile, new_left, ep)


def count_structures(grid: Grid, mode: str) -> int:
    """Exact count of undirected Hamiltonian cycles (mode="cycle") or open
    Hamiltonian paths (mode="path") on `grid`, treating a solution as a set
    of edges (so a path/cycle and its reverse traversal count once)."""
    if mode not in ("cycle", "path"):
        raise ValueError("mode must be 'cycle' or 'path'")

    R, C = grid.rows, grid.cols
    open_mask = [[grid.is_open(r, c) for c in range(C)] for r in range(R)]
    num_open = sum(sum(row) for row in open_mask)

    if num_open == 0:
        return 0
    if num_open == 1:
        return 1 if mode == "path" else 0

    if mode == "cycle":
        black = sum(1 for r in range(R) for c in range(C) if open_mask[r][c] and (r + c) % 2 == 0)
        white = num_open - black
        if black != white:
            return 0

    allow_lone = mode == "path"
    max_endpoints = 2 if allow_lone else 0

    last_open = None
    for r in range(R):
        for c in range(C):
            if open_mask[r][c]:
                last_open = (r, c)

    init_profile: Tuple[int, ...] = tuple([EMPTY] * C)
    states: Dict[State, int] = {(init_profile, EMPTY, 0): 1}

    answer = 0

    for r in range(R):
        has_down = r < R - 1
        for c in range(C):
            has_right = c < C - 1
            is_blocked = not open_mask[r][c]
            is_last = (r, c) == last_open
            next_states: Dict[State, int] = {}

            for (profile, left, ep), ways in states.items():
                combined = profile[:c] + (left,) + profile[c:]
                for outcome in _transition(
                    combined, c, has_right, has_down, is_blocked, is_last, allow_lone, max_endpoints, ep
                ):
                    if outcome[0] == "sol":
                        answer += ways
                    else:
                        _, new_profile, new_left, new_ep = outcome
                        key = (new_profile, new_left, new_ep)
                        next_states[key] = next_states.get(key, 0) + ways

            states = next_states
            if not states:
                return answer

    return answer


def count_paths(grid: Grid) -> int:
    return count_structures(grid, "path")


def count_cycles(grid: Grid) -> int:
    return count_structures(grid, "cycle")
