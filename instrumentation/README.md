# Timing hooks for Qucs-S

`perf-bench-hooks.patch` adds one command-line option to Qucs-S so that GUI
operations can be timed from a script. It applies to the upstream commit
named in `UPSTREAM_COMMIT`. It is measurement tooling only and is not meant
to be merged upstream.

The patch adds `qucs/perf_bench.cpp` and `qucs/perf_bench.h`, registers the
option in `qucs/main.cpp` and adds the source file to `qucs/CMakeLists.txt`.

## What a run does

    qucs-s --perf-bench=/abs/path/file.sch --perf-bench-repeat=20

1. Creates the regular main window (`QucsApp`), 1280x800, and shows it.
2. Opens the schematic through `QucsApp::gotoPage`, the entry point behind
   File > Open.
3. Runs each operation below `--perf-bench-repeat` times, timing every
   repetition with `QElapsedTimer`.
4. Prints one JSON object on stdout and exits.

Repaints go through `QWidget::repaint()`, which paints synchronously, so
each sample is one complete `Schematic::drawContents` pass.

| JSON key | Operation |
|---|---|
| `startup_ms` | create and show the main window |
| `load_ms` | `QucsApp::gotoPage(file)` |
| `first_paint_ms` | pending events plus the first repaint after load |
| `paint_fit_ms[]` | repaint after `showAll()` (zoom to fit) |
| `paint_1to1_ms[]` | repaint after `showNoZoom()` (scale 1.0) |
| `pan_ms[]` | `scrollRight(40)` then repaint |
| `zoom_ms[]` | `zoomBy(1.25)` or `zoomBy(0.8)`, alternating, then repaint |
| `undo_snapshot_ms[]` | `setChanged(true, true)`, the bookkeeping done after every edit |

The object also carries `schema`, `file`, `components`, `wires`, `nodes`,
`viewport_w`, `viewport_h`, `scale_fit`, `qt_version` and `qt_platform`.

Exit codes: `0` success, `2` the schematic could not be loaded, `3` a modal
dialog appeared (its text is printed on stderr).

## Things that block a headless run

- **The option must be one argument.** Qucs-S opens every argument that does
  not start with a dash as a document, so `--perf-bench FILE` would load the
  file twice. Use `--perf-bench=FILE`.
- **First-run dialog.** A fresh profile triggers a "Set simulator" message
  box in the `QucsApp` constructor. The hooks pin the related settings
  before creating the window.
- **Dataset names.** If `<DataSet=...>` and `<DataDisplay=...>` in the
  schematic do not match the file name, loading asks whether to fix them.
  Generated schematics must use matching names.
- Any other modal dialog is detected by a watchdog timer and reported with
  exit code 3 instead of hanging.

## Updating the patch

Commit the changed hooks on a local branch of a Qucs-S checkout based on the
pinned commit, then regenerate the patch from that commit:

    git -C "$QUCS_S_SRC" diff "$(cat instrumentation/UPSTREAM_COMMIT)" HEAD -- \
        qucs/perf_bench.cpp qucs/perf_bench.h qucs/main.cpp qucs/CMakeLists.txt \
        > instrumentation/perf-bench-hooks.patch
