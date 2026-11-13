# Method

This page says what is measured, under which conditions, and how a change
is judged. The rule behind all of it: a number is only reported if someone
else can run a command from this repository and get a comparable one.

## What is measured

Qucs-S is built from a pinned upstream commit with a small patch that adds
timing hooks ([instrumentation/](../instrumentation/README.md)). One run of
the hooks opens a schematic in the regular main window and times:

- loading the file,
- repainting the whole view at zoom-to-fit and at scale 1.0,
- one pan step and one zoom step, each followed by a repaint,
- the undo snapshot taken after every edit.

The window is rendered through Qt's `offscreen` platform. Widgets are
painted by the same raster engine as on a desktop session; what is left out
is the final copy to the screen and the compositor. The numbers are
therefore CPU time spent in Qucs-S and Qt, not end-to-end latency.

Inputs are generated schematics of increasing size, so that the growth of
each operation with the number of components is visible, not only its
absolute cost on one file.

## Conditions

Timings depend on the machine state, so the state is fixed where possible
and recorded always (`python3 -m bench.environment`).

| Setting | Value on the reference machine | Why |
|---|---|---|
| CPU | Intel Core i5-1245U, 2 performance cores, 8 efficiency cores | |
| Pinning | `taskset -c 0`, a performance core | the two core types differ by a large factor |
| Turbo | disabled (`intel_pstate/no_turbo` = 1) | frequency no longer depends on temperature |
| Governor | `performance`, 1.6 GHz maximum | no ramp-up at the start of a run |
| Power | on AC | |
| Build | RelWithDebInfo, `-fno-omit-frame-pointer` | optimised code with usable call stacks |
| Qt | 6.4.2 (Ubuntu 24.04 packages), `offscreen` platform | |
| Settings | private `HOME` per measurement | the user's Qucs-S configuration is not involved |

Absolute values are specific to this machine, which runs at a fixed and
fairly low frequency. Ratios between sizes, and between before and after a
change, are what the study reports.

## Statistics

Each operation is sampled several times inside one process, and each
scenario is run in several separate processes. Load time gives one sample
per process; paint operations give `repeat` samples per process.

The median is the reported value. It is not moved by the occasional slow
sample caused by an interrupt or a page fault. The spread (minimum, and
interquartile range) is reported next to it, because a difference between
two medians only means something when it is larger than the spread.

Raw samples are kept in the result files. A summary cannot be re-analysed;
samples can.

## Profiles

`scripts/profile.sh` records the same hook run under `perf record` with
frame-pointer unwinding at 999 Hz, then writes the folded stacks and a
flame graph to `results/profiles/`. The recording can be opened in Hotspot
for interactive inspection.

A flame graph shows where samples were taken, with callers below callees.
Width is share of samples, not duration of one call. It answers "which code
is the time in", which is the question to settle before changing anything.

## Judging a change

Every candidate change goes through the same loop, run by a script so that
no step depends on who or what proposed the change:

1. apply the candidate to the Qucs-S source tree,
2. rebuild the instrumented binary,
3. run the scenarios,
4. compare each operation with the stored baseline,
5. keep the change if it is faster by more than the measurement noise and
   slows nothing else down by more than the noise; reject it otherwise,
6. append the proposal, the numbers and the decision to a log.

Rejected proposals stay in the log. A change that looked reasonable and
measured as useless is a result too.

Each kept change is documented with a profile from before and after, so the
claim "this function no longer dominates" can be checked against the flame
graphs and not only against a timing table.
