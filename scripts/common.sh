# Shared settings for the scripts in this directory. Source, do not execute.
#
# Environment overrides:
#   QUCS_S_SRC    Qucs-S source tree        (default: .cache/qucs_s)
#   QUCS_S_BUILD  Qucs-S build directory    (default: .cache/build-relwithdebinfo)
#   QUCS_S_BIN    instrumented qucs-s binary (default: $QUCS_S_BUILD/qucs/qucs-s)
#   BENCH_CPU     CPU the benchmark is pinned to (default: 0)

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUCS_S_SRC="${QUCS_S_SRC:-$REPO_ROOT/.cache/qucs_s}"
QUCS_S_BUILD="${QUCS_S_BUILD:-$REPO_ROOT/.cache/build-relwithdebinfo}"
QUCS_S_BIN="${QUCS_S_BIN:-$QUCS_S_BUILD/qucs/qucs-s}"
BENCH_CPU="${BENCH_CPU:-0}"
UPSTREAM_URL="https://github.com/ra3xdh/qucs_s.git"
UPSTREAM_COMMIT="$(cat "$REPO_ROOT/instrumentation/UPSTREAM_COMMIT")"
HOOKS_PATCH="$REPO_ROOT/instrumentation/perf-bench-hooks.patch"

die() { echo "error: $*" >&2; exit 1; }

# Runs a command with the settings every measurement uses: a private HOME so
# the user's Qucs-S configuration is neither read nor modified, the offscreen
# Qt platform, and one fixed CPU.
bench_exec() {
    local bench_home="$REPO_ROOT/.cache/bench-home"
    mkdir -p "$bench_home"
    HOME="$bench_home" XDG_CONFIG_HOME="$bench_home/.config" \
    QT_QPA_PLATFORM=offscreen LC_ALL=C \
        taskset -c "$BENCH_CPU" "$@"
}
