"""Grid representation for Hamiltonian path/cycle problems."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

Cell = tuple[int, int]

# 4-connectivity neighbor offsets: right, down, left, up
_DIRECTIONS: tuple[Cell, ...] = ((0, 1), (1, 0), (0, -1), (-1, 0))


@dataclass(frozen=True)
class Grid:
    """A rectangular grid of `rows` x `cols` cells, some of which may be blocked.

    Cells are addressed as (row, col) with row in [0, rows) and col in [0, cols).
    """

    rows: int
    cols: int
    blocked: frozenset[Cell] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.rows < 1 or self.cols < 1:
            raise ValueError("Grid must have at least 1 row and 1 column")
        for r, c in self.blocked:
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                raise ValueError(f"Blocked cell {(r, c)} is outside the {self.rows}x{self.cols} grid")

    def is_open(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols and (r, c) not in self.blocked

    @property
    def num_open(self) -> int:
        return self.rows * self.cols - len(self.blocked)

    def open_cells(self) -> Iterator[Cell]:
        for r in range(self.rows):
            for c in range(self.cols):
                if self.is_open(r, c):
                    yield (r, c)

    def neighbors(self, r: int, c: int) -> Iterator[Cell]:
        for dr, dc in _DIRECTIONS:
            nr, nc = r + dr, c + dc
            if self.is_open(nr, nc):
                yield (nr, nc)

    def transposed(self) -> "Grid":
        """Return a new Grid with rows/cols swapped (row<->col for every cell)."""
        return Grid(
            rows=self.cols,
            cols=self.rows,
            blocked=frozenset((c, r) for r, c in self.blocked),
        )

    def shape_key(self) -> tuple[int, int, frozenset[Cell]]:
        return (self.rows, self.cols, self.blocked)

    @staticmethod
    def full(rows: int, cols: int) -> "Grid":
        """A grid with no blocked cells."""
        return Grid(rows=rows, cols=cols, blocked=frozenset())

    @staticmethod
    def from_blocked(rows: int, cols: int, blocked: Iterable[Cell]) -> "Grid":
        return Grid(rows=rows, cols=cols, blocked=frozenset(blocked))

    @staticmethod
    def from_ascii(pattern: str, open_char: str = ".", blocked_char: str = "#") -> "Grid":
        """Build a grid from a multi-line ASCII pattern, e.g.:

            ...
            .#.
            ...

        `open_char` marks open cells, `blocked_char` marks blocked cells.
        Leading/trailing blank lines are ignored; all rows must have equal length.
        """
        lines = [line for line in pattern.splitlines() if line.strip() != ""]
        if not lines:
            raise ValueError("Empty pattern")
        rows = len(lines)
        cols = len(lines[0])
        blocked: set[Cell] = set()
        for r, line in enumerate(lines):
            if len(line) != cols:
                raise ValueError("All rows in the ASCII pattern must have the same length")
            for c, ch in enumerate(line):
                if ch == blocked_char:
                    blocked.add((r, c))
                elif ch != open_char:
                    raise ValueError(f"Unexpected character {ch!r} in pattern")
        return Grid(rows=rows, cols=cols, blocked=frozenset(blocked))

    def to_ascii(self, open_char: str = ".", blocked_char: str = "#") -> str:
        lines = []
        for r in range(self.rows):
            lines.append("".join(blocked_char if (r, c) in self.blocked else open_char for c in range(self.cols)))
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_ascii()
