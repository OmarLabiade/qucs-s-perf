#!/usr/bin/env bash
# Runs the timing hooks once on a schematic and prints the raw JSON line.
#
# Usage: scripts/run_once.sh SCHEMATIC.sch [SAMPLES]
#   SAMPLES  samples per timed operation inside the process (default 20)
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

[[ $# -ge 1 ]] || die "usage: $0 SCHEMATIC.sch [SAMPLES]"
schematic="$(realpath "$1")"
samples="${2:-20}"

[[ -x "$QUCS_S_BIN" ]] || die "$QUCS_S_BIN not found, run scripts/build_qucs.sh first"
[[ -f "$schematic" ]] || die "no such schematic: $schematic"

# --perf-bench=FILE must be a single argument: Qucs-S opens every argument
# that does not start with a dash as a document.
bench_exec "$QUCS_S_BIN" "--perf-bench=$schematic" "--perf-bench-repeat=$samples" 2>/dev/null
