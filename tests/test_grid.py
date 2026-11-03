from hamiltonian.grid import Grid


def test_full_grid_open_cells():
    g = Grid.full(2, 3)
    assert g.num_open == 6
    assert list(g.open_cells()) == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]


def test_blocked_cells():
    g = Grid.from_blocked(3, 3, [(1, 1)])
    assert g.num_open == 8
    assert not g.is_open(1, 1)
    assert set(g.neighbors(0, 1)) == {(0, 0), (0, 2)}


def test_ascii_roundtrip():
    pattern = "...\n.#.\n..."
    g = Grid.from_ascii(pattern)
    assert g.rows == 3 and g.cols == 3
    assert g.blocked == frozenset({(1, 1)})
    assert g.to_ascii() == pattern


def test_transpose():
    g = Grid.from_blocked(2, 3, [(0, 2)])
    t = g.transposed()
    assert t.rows == 3 and t.cols == 2
    assert t.blocked == frozenset({(2, 0)})


def test_out_of_bounds_blocked_cell_rejected():
    import pytest

    with pytest.raises(ValueError):
        Grid.from_blocked(2, 2, [(5, 5)])
