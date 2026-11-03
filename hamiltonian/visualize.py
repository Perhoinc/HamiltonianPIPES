"""Matplotlib visualizations: one example solution path drawn on its grid,
and a plot of how the solution count scales with grid size."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .dataset import SizeResult
from .grid import Cell, Grid


def draw_solution(
    grid: Grid,
    path: list[Cell],
    is_cycle: bool,
    title: Optional[str] = None,
    save_path: Optional[str | Path] = None,
    ax=None,
):
    """Draw the grid (blocked cells shaded) with the given path/cycle
    overlaid as a connected line from cell to cell, colored start-to-end and
    numbered in visiting order."""
    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(max(4, grid.cols * 0.9), max(4, grid.rows * 0.9)))

    ax.set_xlim(-0.5, grid.cols - 0.5)
    ax.set_ylim(-0.5, grid.rows - 0.5)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_xticks(range(grid.cols))
    ax.set_yticks(range(grid.rows))
    ax.grid(True, color="#dddddd", linewidth=0.5)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    for r in range(grid.rows):
        for c in range(grid.cols):
            if (r, c) in grid.blocked:
                ax.add_patch(Rectangle((c - 0.5, r - 0.5), 1, 1, facecolor="#333333", edgecolor="none"))
            else:
                ax.add_patch(Rectangle((c - 0.5, r - 0.5), 1, 1, facecolor="#f5f5f5", edgecolor="none", zorder=0))

    n = len(path)
    cmap = plt.get_cmap("viridis")
    xs = [c for (_, c) in path]
    ys = [r for (r, _) in path]

    segments = list(zip(path, path[1:]))
    if is_cycle and n > 1:
        segments.append((path[-1], path[0]))

    for i, ((r1, c1), (r2, c2)) in enumerate(segments):
        color = cmap(i / max(1, len(segments) - 1))
        ax.plot([c1, c2], [r1, r2], color=color, linewidth=3, solid_capstyle="round", zorder=2)

    ax.scatter(xs, ys, color=[cmap(i / max(1, n - 1)) for i in range(n)], s=90, zorder=3, edgecolors="white", linewidths=1)
    ax.scatter([xs[0]], [ys[0]], s=220, facecolors="none", edgecolors="black", linewidths=2, zorder=4, label="start")
    if not is_cycle:
        ax.scatter([xs[-1]], [ys[-1]], s=220, marker="s", facecolors="none", edgecolors="black", linewidths=2, zorder=4, label="end")

    kind = "Hamiltonian cycle" if is_cycle else "Hamiltonian path"
    ax.set_title(title or f"Example {kind} on a {grid.rows}x{grid.cols} grid ({n} cells)")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

    if own_fig and save_path:
        fig.tight_layout()
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
    return ax


def plot_scaling(
    results: list[SizeResult],
    save_path: Optional[str | Path] = None,
    log_scale: bool = True,
):
    """Line plot of Hamiltonian path/cycle counts vs. square grid size N."""
    ns = [r.n for r in results]
    paths = [r.num_paths for r in results]
    cycles = [r.num_cycles for r in results]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(ns, paths, marker="o", label="Hamiltonian paths", color="#2563eb")
    ax.plot(ns, cycles, marker="s", label="Hamiltonian cycles", color="#dc2626")

    if log_scale:
        ax.set_yscale("log")
    ax.set_xlabel("Grid size (N, for an N x N grid)")
    ax.set_ylabel("Number of distinct solutions" + (" (log scale)" if log_scale else ""))
    ax.set_title("Hamiltonian path/cycle count vs. grid size")
    ax.set_xticks(ns)
    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.6)
    ax.legend()

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
    return fig, ax
