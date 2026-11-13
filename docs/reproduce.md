# How to reproduce

Commands are run from the root of this repository on Ubuntu 24.04.

## 1. Install the prerequisites

    sudo apt-get install build-essential git cmake ninja-build ccache \
        qt6-base-dev qt6-tools-dev qt6-tools-dev-tools qt6-l10n-tools \
        linguist-qt6 libqt6svg6-dev libgl1-mesa-dev libqt6opengl6-dev \
        flex bison gperf dos2unix \
        linux-tools-common linux-tools-generic hotspot python3-pytest

`perf` needs permission to sample your own processes:

    sudo sysctl kernel.perf_event_paranoid=1

## 2. Build and test this repository

    cmake -G Ninja -S . -B build
    cmake --build build
    ctest --test-dir build --output-on-failure
    python3 -m pytest -q

## 3. Build the instrumented Qucs-S

    scripts/build_qucs.sh

The script fetches Qucs-S at the pinned commit into `.cache/qucs_s`,
applies `instrumentation/perf-bench-hooks.patch` and builds the `qucs-s`
target. A cold build of all Qucs-S targets took 14 minutes on the reference
machine; the `qucs-s` target alone is a subset of that.

To use an existing checkout and build directory instead:

    export QUCS_S_SRC=/path/to/qucs_s
    export QUCS_S_BUILD=/path/to/build
    scripts/build_qucs.sh

An existing source tree is built as it is, which is how a modified Qucs-S
is measured.

## 4. Run the timing hooks once

    scripts/run_once.sh .cache/qucs_s/examples/ngspice/Miscellaneous/example_sub_subcircuit.sch

This prints one JSON line; the keys are described in
[instrumentation/README.md](../instrumentation/README.md).

## 5. Record a profile

    scripts/profile.sh path/to/file.sch my-label
    hotspot results/profiles/my-label.perf.data

The script prints the frames with the largest inclusive share and writes
`results/profiles/my-label.svg`.

## 6. Record the machine state

    python3 -m bench.environment

Compare the output with the table in [method.md](method.md) before
comparing any timing with the ones in `results/`.
