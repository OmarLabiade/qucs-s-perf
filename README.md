# qucs-s-perf

A performance study of the schematic editor of
[Qucs-S](https://github.com/ra3xdh/qucs_s), a C++/Qt circuit simulation
front end: where does the GUI spend its time on large schematics, and which
changes make it measurably faster?

[![CI](https://github.com/OmarLabiade/qucs-s-perf/actions/workflows/ci.yml/badge.svg)](https://github.com/OmarLabiade/qucs-s-perf/actions/workflows/ci.yml)

## Goal

1. Define reproducible scenarios: generated schematics from 1,000 to 20,000
   components, and a fixed set of GUI operations on each (load, repaint,
   pan, zoom, edit bookkeeping).
2. Measure a baseline and profile it with `perf` and Hotspot.
3. Fix one or two of the bottlenecks the profiles point at, and show the
   effect with before/after timings and flame graphs.
4. Propose the fixes upstream.

Candidate changes are evaluated by a script, not by eye: it applies the
change, rebuilds, runs the scenarios, compares with the baseline and keeps
or rejects the change. The same loop is used whether a change comes from a
person or from an AI coding agent, and every proposal is logged with its
numbers, including the rejected ones.

## Platform and prerequisites

Developed and measured on Ubuntu 24.04 (x86-64) with GCC 13, Qt 6.4,
CMake 3.28, Python 3.12, `perf` 6.8 and Hotspot 1.3. The full package list
is in [docs/reproduce.md](docs/reproduce.md).

All timings in this repository come from one machine, described in
[docs/method.md](docs/method.md). Absolute values will differ elsewhere;
the method is what carries over.

## Build and run

    # this repository: microbench support library and tests
    cmake -G Ninja -S . -B build
    cmake --build build
    ctest --test-dir build --output-on-failure
    python3 -m pytest -q

    # Qucs-S at the pinned commit, with the timing hooks
    scripts/build_qucs.sh

    # one timed run on a schematic, raw JSON on stdout
    scripts/run_once.sh path/to/file.sch

    # CPU profile and flame graph of the same run
    scripts/profile.sh path/to/file.sch my-label

## Measurement pipeline

    scenarios/  ->  instrumented qucs-s  ->  bench/  ->  results/
    generated       --perf-bench=FILE        N runs,     raw timings,
    schematics      JSON per run             median      tables, flame graphs
                          ^                     |
                          |                     v
                    candidate change  <-  agent/ : compare with baseline,
                                                   keep or reject, log

- **Timing hooks.** A small patch
  ([instrumentation/](instrumentation/README.md)) adds
  `qucs-s --perf-bench=FILE`. It opens the schematic in the real main
  window, rendered offscreen, times each operation with `QElapsedTimer` and
  prints one JSON object.
- **Controlled conditions.** Every run is pinned to one performance core
  and uses a private settings directory. The machine state is recorded with
  each result set (`python3 -m bench.environment`).
- **Profiles.** `scripts/profile.sh` runs the same hooks under
  `perf record` and writes folded stacks and a flame graph to
  `results/profiles/`; the recording opens in Hotspot.

## Repository layout

| Directory | Content |
|---|---|
| `instrumentation/` | timing hooks patch for Qucs-S and the pinned upstream commit |
| `scripts/` | build, single run and profiling scripts |
| `bench/` | measurement environment and flame graph tooling (Python) |
| `microbench/` | small Qt program comparing ways to draw N items (C++) |
| `tests/` | Python tests |
| `results/` | measured data and figures |
| `docs/` | method, code notes, how to reproduce |

## Roadmap

| Step | Status |
|---|---|
| Build Qucs-S in RelWithDebInfo, run it headless | done |
| Timing hooks (`--perf-bench`) and build script | done |
| Profiling script, folded stacks, flame graphs | done |
| Measurement environment and machine state record | done |
| Microbench: command line, statistics, report | done |
| Microbench: paint-all, paint-visible and QGraphicsView backends | planned |
| Scenario generator, 1,000 to 20,000 components | planned |
| Baseline harness: N runs per scenario, median, CSV/JSON | planned |
| Baseline profiles and ranked bottlenecks | planned |
| Evaluation loop for candidate changes, with proposal log | planned |
| Fixes in a Qucs-S fork, before/after numbers and flame graphs | planned |
| Write-up and upstream proposal | planned |

## First observations

From reading the code ([docs/code-notes.md](docs/code-notes.md)):

- the schematic view is painted by hand, and every repaint draws every
  element, visible or not;
- loading looks up each connection point by scanning all existing ones, so
  load time grows with the square of the schematic size;
- every edit serialises the whole document for undo.

An exploratory run of the timing hooks on a grid of 10,000 resistors
agrees with this reading: about 20 s to load and 0.22 to 0.25 s per repaint,
at any zoom level. These figures predate the scenario generator and the
harness; the reproducible baseline will replace them in `results/`.

## Resources

- Qucs-S: <https://github.com/ra3xdh/qucs_s>
- `perf` wiki: <https://perf.wiki.kernel.org/>
- Hotspot, a GUI for perf data: <https://github.com/KDAB/hotspot>
- Brendan Gregg, Flame Graphs: <https://www.brendangregg.com/flamegraphs.html>
- Qt documentation, Graphics View Framework: <https://doc.qt.io/qt-6/graphicsview.html>
- Qt documentation, Paint System: <https://doc.qt.io/qt-6/paintsystem.html>

## License

GPL-2.0-or-later, the license of Qucs-S, whose source the timing hooks
patch modifies. See [LICENSE](LICENSE).
