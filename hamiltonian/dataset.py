"""Generate the count-vs-grid-size dataset (square grids N x N for N in a
given range, both path and cycle counts) using the exact profile DP."""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path

from .counting import count_cycles, count_paths
from .grid import Grid


@dataclass
class SizeResult:
    n: int
    num_paths: int
    num_cycles: int
    path_seconds: float
    cycle_seconds: float


def generate_square_dataset(
    min_n: int = 2,
    max_n: int = 10,
    progress: bool = True,
) -> list[SizeResult]:
    """Compute exact Hamiltonian path and cycle counts for every N x N
    square grid with N from `min_n` to `max_n` inclusive."""
    results = []
    for n in range(min_n, max_n + 1):
        grid = Grid.full(n, n)

        t0 = time.perf_counter()
        num_paths = count_paths(grid)
        t1 = time.perf_counter()
        num_cycles = count_cycles(grid)
        t2 = time.perf_counter()

        result = SizeResult(
            n=n,
            num_paths=num_paths,
            num_cycles=num_cycles,
            path_seconds=t1 - t0,
            cycle_seconds=t2 - t1,
        )
        results.append(result)
        if progress:
            print(
                f"{n}x{n}: paths={num_paths:,} ({result.path_seconds:.2f}s)  "
                f"cycles={num_cycles:,} ({result.cycle_seconds:.2f}s)"
            )
    return results


def save_csv(results: list[SizeResult], path: str | Path) -> None:
    path = Path(path)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["n", "num_paths", "num_cycles", "path_seconds", "cycle_seconds"])
        for r in results:
            writer.writerow([r.n, r.num_paths, r.num_cycles, f"{r.path_seconds:.4f}", f"{r.cycle_seconds:.4f}"])


def save_json(results: list[SizeResult], path: str | Path) -> None:
    path = Path(path)
    payload = [
        {
            "n": r.n,
            "grid": f"{r.n}x{r.n}",
            "num_paths": r.num_paths,
            "num_cycles": r.num_cycles,
            "path_seconds": round(r.path_seconds, 4),
            "cycle_seconds": round(r.cycle_seconds, 4),
        }
        for r in results
    ]
    path.write_text(json.dumps(payload, indent=2) + "\n")


def load_json(path: str | Path) -> list[SizeResult]:
    payload = json.loads(Path(path).read_text())
    return [
        SizeResult(
            n=item["n"],
            num_paths=item["num_paths"],
            num_cycles=item["num_cycles"],
            path_seconds=item.get("path_seconds", 0.0),
            cycle_seconds=item.get("cycle_seconds", 0.0),
        )
        for item in payload
    ]
