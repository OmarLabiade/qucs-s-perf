#!/usr/bin/env bash
# Builds the instrumented qucs-s binary used by every measurement.
#
# Fetches Qucs-S at the pinned upstream commit if no source tree exists,
# applies the timing hooks if they are not there yet, then builds the
# `qucs-s` target in RelWithDebInfo with frame pointers.
#
# An existing source tree is built as it is: whatever is checked out there
# (the baseline or a candidate change) is what gets measured.
#
# Usage: scripts/build_qucs.sh
# Prints the path of the binary on the last line.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

if [[ ! -d "$QUCS_S_SRC/.git" && ! -f "$QUCS_S_SRC/.git" ]]; then
    echo ">> fetching Qucs-S $UPSTREAM_COMMIT into $QUCS_S_SRC"
    git init -q "$QUCS_S_SRC"
    git -C "$QUCS_S_SRC" remote add origin "$UPSTREAM_URL"
    git -C "$QUCS_S_SRC" fetch -q --depth 1 origin "$UPSTREAM_COMMIT"
    git -C "$QUCS_S_SRC" checkout -q --detach FETCH_HEAD
fi

if [[ ! -f "$QUCS_S_SRC/qucs/perf_bench.cpp" ]]; then
    echo ">> applying timing hooks"
    git -C "$QUCS_S_SRC" apply "$HOOKS_PATCH" \
        || die "the hooks patch does not apply to $(git -C "$QUCS_S_SRC" rev-parse --short HEAD)"
fi

launcher=()
if command -v ccache >/dev/null; then
    launcher=(-DCMAKE_CXX_COMPILER_LAUNCHER=ccache)
fi

if [[ ! -f "$QUCS_S_BUILD/build.ninja" ]]; then
    echo ">> configuring $QUCS_S_BUILD"
    cmake -G Ninja -S "$QUCS_S_SRC" -B "$QUCS_S_BUILD" \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DCMAKE_CXX_FLAGS="-fno-omit-frame-pointer" \
        "${launcher[@]}" >/dev/null
fi

echo ">> building qucs-s ($(git -C "$QUCS_S_SRC" rev-parse --short HEAD))"
cmake --build "$QUCS_S_BUILD" --target qucs-s

[[ -x "$QUCS_S_BIN" ]] || die "build finished but $QUCS_S_BIN is missing"
echo "$QUCS_S_BIN"
