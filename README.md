# HamiltonianPIPES

Hamiltonian path & cycle counter and visualizer for 2D grids.

A curiosity-driven tool: how many distinct ways are there to walk through
every cell of an N×N grid, visiting each exactly once? How does that count
grow as the grid gets bigger? What does one of those routes actually look
like? This explores exactly that, for grids from 2×2 up to 10×10, including
grids with blocked cells (so paths have to route around holes / arbitrary
shapes).

This is a standalone project, unrelated to PIPEGRID.

## What it computes

- **Hamiltonian path**: a route that visits every open cell of the grid
  exactly once.
- **Hamiltonian cycle**: same, but the route also returns to its starting
  cell (so it forms a loop).

Counts are of *distinct routes* — a path/cycle and its reverse traversal
are the same route, so they're counted once, not twice.

## Why this needed more than brute force

The number of solutions explodes fast. A 10×10 grid has **730,044,829,512,632**
distinct Hamiltonian paths and **467,260,456,608** distinct Hamiltonian
cycles — there is no enumerating those one at a time. Instead,
[`hamiltonian/profile_dp.py`](hamiltonian/profile_dp.py) implements a
"broken profile" (a.k.a. connectivity / plug) dynamic program: it sweeps
the grid cell by cell and tracks, along the boundary between the processed
and unprocessed region, which cells have a dangling path edge and which
other dangling edge each one is destined to connect to. This lets it count
every solution without ever constructing one, in time polynomial in the
grid area (a few seconds for the full 10×10, see `data/counts.csv`).

This is cross-validated against exhaustive brute-force enumeration
(`hamiltonian/brute_force.py`) on dozens of small grid shapes — rectangular,
with holes, degenerate — in `tests/test_cross_validate.py`, plus a larger
randomized fuzz run during development. As an independent sanity check, the
computed sequences for plain N×N grids match the published OEIS sequences
[A096969](https://oeis.org/A096969) (Hamiltonian paths) and
[A003763](https://oeis.org/A003763) (Hamiltonian cycles on 2n×2n grids).

For visualizing *one example* solution (not counting), a much simpler
DFS with Warnsdorff's-rule ordering and connectivity pruning
(`hamiltonian/brute_force.py`) finds a single path/cycle quickly, even on
grids too large to enumerate exhaustively.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Use it

```bash
# Exact counts for a grid, with some cells blocked (row,col pairs)
python cli.py count --rows 6 --cols 6 --blocked 2,2 3,3

# Or load an arbitrary shape from an ASCII file ('.'=open, '#'=blocked)
python cli.py count --shape shapes/plus.txt

# Draw one example solution to a PNG
python cli.py visualize --rows 10 --cols 10 --kind path  --out figures/my_path.png
python cli.py visualize --rows 10 --cols 10 --kind cycle --out figures/my_cycle.png
python cli.py visualize --shape shapes/plus.txt --kind path --out figures/my_plus.png

# Regenerate the full 2x2..10x10 scaling dataset + plot
python cli.py dataset --min-n 2 --max-n 10 --out-dir data --figure figures/scaling_plot.png
```

Run the test suite (includes the brute-force cross-validation):

```bash
python -m pytest tests/ -q
```

## Results

Exact counts for every N×N grid from 2×2 to 10×10 (`data/counts.csv` /
`data/counts.json`):

| N   | Hamiltonian paths | Hamiltonian cycles |
|-----|-------------------:|--------------------:|
| 2   | 4 | 1 |
| 3   | 20 | 0 |
| 4   | 276 | 6 |
| 5   | 4,324 | 0 |
| 6   | 229,348 | 1,072 |
| 7   | 13,535,280 | 0 |
| 8   | 3,023,313,284 | 4,638,576 |
| 9   | 745,416,341,496 | 0 |
| 10  | 730,044,829,512,632 | 467,260,456,608 |

Odd-sized grids always have **0** Hamiltonian cycles: a grid graph is
bipartite (checkerboard-colorable), and a cycle must alternate colors, so
it needs equal numbers of each — impossible when the total cell count is
odd.

![Count vs grid size](figures/scaling_plot.png)

An example Hamiltonian cycle on the full 10×10 grid:

![Example 10x10 cycle](figures/example_cycle_10x10.png)

An example Hamiltonian path on a plus-shaped grid with blocked corners
(`shapes/plus.txt`):

![Example path on a plus-shaped grid](figures/example_plus_path.png)

## Interactive web version

[`web/hamilton-loom.html`](web/hamilton-loom.html) is a self-contained, no-install
GUI: open it in any browser to click cells to cut holes into a grid, see the
exact path/cycle counts update live, and watch an example route trace itself
onto the grid. It's a JavaScript port of the same broken-profile DP and
Warnsdorff-search algorithms as the Python package (validated against the
Python implementation's outputs, including the full 10x10 case), running in
a Web Worker so the page stays responsive during a multi-second count. No
build step or server needed — just open the file.

It also supports **browsing solutions by number** instead of only random
ones: "Browse paths"/"Browse cycles" shows "Solution *k* of *total*" with
Prev/Next and a jump-to-# field. This extends the DP into an *unranking*
algorithm — given index *k*, it reconstructs the exact *k*-th solution
directly (via a one-time forward+backward pass building per-step
completion counts), rather than generating and discarding the ones before
it. Exhaustively verified against brute-force enumeration (every index,
not a sample) across dozens of grid shapes before shipping.

## Project layout

```
hamiltonian/
  grid.py         Grid representation (rows, cols, blocked cells, ASCII I/O)
  profile_dp.py   Exact polynomial-time counter (broken-profile / plug DP)
  brute_force.py  Exhaustive counter (test ground truth) + fast single-
                   solution finder (for visualization)
  counting.py     Unified count_paths / count_cycles / example_path /
                   example_cycle interface
  dataset.py      Generates the N x N scaling dataset
  visualize.py    matplotlib rendering (example solution, scaling plot)
cli.py            Command-line entry point
tests/            pytest suite, including brute-force cross-validation
shapes/           example ASCII grid shapes
data/             generated counts.csv / counts.json
figures/          generated PNGs
web/              standalone interactive HTML GUI (JS port of the algorithm)
```

## Non-goals (for now)

- 3D grids (possible future extension)
- Any integration with PIPEGRID — this is fully standalone
