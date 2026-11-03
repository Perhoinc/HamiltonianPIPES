#!/usr/bin/env python3
"""Command-line entry point for the Hamiltonian Path Counter & Visualizer.

Examples:
    # Exact counts for a plain grid
    python cli.py count --rows 6 --cols 6

    # Same, but with some cells blocked (row,col pairs)
    python cli.py count --rows 5 --cols 5 --blocked 2,2 2,1

    # Load a grid shape from an ASCII file (. = open, # = blocked)
    python cli.py count --shape shapes/example.txt

    # Draw one example path/cycle to a PNG
    python cli.py visualize --rows 10 --cols 10 --kind path --out figures/out.png
    python cli.py visualize --rows 10 --cols 10 --kind cycle --out figures/out.png

    # Regenerate the full 2x2..10x10 scaling dataset + plot
    python cli.py dataset --min-n 2 --max-n 10 --out-dir data --figure figures/scaling_plot.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hamiltonian.counting import count_cycles, count_paths, example_cycle, example_path
from hamiltonian.dataset import generate_square_dataset, save_csv, save_json
from hamiltonian.grid import Grid
from hamiltonian.visualize import draw_solution, plot_scaling


def _parse_cell(s: str) -> tuple[int, int]:
    r, c = s.split(",")
    return (int(r), int(c))


def _grid_from_args(args) -> Grid:
    if args.shape:
        text = Path(args.shape).read_text()
        return Grid.from_ascii(text)
    if args.rows is None or args.cols is None:
        raise SystemExit("Either --shape or both --rows and --cols are required")
    blocked = [_parse_cell(s) for s in (args.blocked or [])]
    return Grid.from_blocked(args.rows, args.cols, blocked)


def _add_grid_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--rows", type=int, help="number of rows (2-10 typical)")
    p.add_argument("--cols", type=int, help="number of columns (2-10 typical)")
    p.add_argument("--blocked", nargs="*", help="blocked cells as 'row,col' pairs, e.g. 1,1 2,3")
    p.add_argument("--shape", help="path to an ASCII grid file ('.'=open, '#'=blocked) instead of --rows/--cols/--blocked")


def cmd_count(args) -> None:
    grid = _grid_from_args(args)
    print(grid)
    print(f"open cells: {grid.num_open}")
    if args.kind in ("path", "both"):
        n = count_paths(grid)
        print(f"Hamiltonian paths:  {n:,}")
    if args.kind in ("cycle", "both"):
        n = count_cycles(grid)
        print(f"Hamiltonian cycles: {n:,}")


def cmd_visualize(args) -> None:
    grid = _grid_from_args(args)
    if args.kind == "cycle":
        sol = example_cycle(grid, seed=args.seed)
    else:
        sol = example_path(grid, seed=args.seed)
    if sol is None:
        print(f"No Hamiltonian {args.kind} exists for this grid.")
        sys.exit(1)
    out = args.out or f"figures/example_{args.kind}_{grid.rows}x{grid.cols}.png"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    draw_solution(grid, sol, is_cycle=(args.kind == "cycle"), save_path=out)
    print(f"Saved {args.kind} covering {len(sol)} cells to {out}")


def cmd_dataset(args) -> None:
    results = generate_square_dataset(args.min_n, args.max_n)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    save_csv(results, out_dir / "counts.csv")
    save_json(results, out_dir / "counts.json")
    print(f"Saved {out_dir / 'counts.csv'} and {out_dir / 'counts.json'}")
    if args.figure:
        Path(args.figure).parent.mkdir(parents=True, exist_ok=True)
        plot_scaling(results, save_path=args.figure)
        print(f"Saved scaling plot to {args.figure}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hamiltonian Path Counter & Visualizer")
    sub = parser.add_subparsers(dest="command", required=True)

    p_count = sub.add_parser("count", help="exact Hamiltonian path/cycle count for one grid")
    _add_grid_args(p_count)
    p_count.add_argument("--kind", choices=["path", "cycle", "both"], default="both")
    p_count.set_defaults(func=cmd_count)

    p_vis = sub.add_parser("visualize", help="draw one example path/cycle to a PNG")
    _add_grid_args(p_vis)
    p_vis.add_argument("--kind", choices=["path", "cycle"], default="path")
    p_vis.add_argument("--seed", type=int, default=None)
    p_vis.add_argument("--out", default=None)
    p_vis.set_defaults(func=cmd_visualize)

    p_data = sub.add_parser("dataset", help="regenerate the N x N scaling dataset + plot")
    p_data.add_argument("--min-n", type=int, default=2)
    p_data.add_argument("--max-n", type=int, default=10)
    p_data.add_argument("--out-dir", default="data")
    p_data.add_argument("--figure", default="figures/scaling_plot.png")
    p_data.set_defaults(func=cmd_dataset)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
