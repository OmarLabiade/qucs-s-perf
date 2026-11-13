#!/usr/bin/env bash
# Records a CPU profile of the timing hooks on one schematic and turns it
# into a flame graph.
#
# Usage: scripts/profile.sh SCHEMATIC.sch LABEL [SAMPLES]
#
# Writes into results/profiles/:
#   LABEL.perf.data   raw recording, open it with `hotspot` (not committed)
#   LABEL.folded      folded stacks (text, one line per distinct stack)
#   LABEL.svg         flame graph rendered from the folded stacks
#
# Call stacks are unwound through frame pointers. The qucs-s binary is built
# with -fno-omit-frame-pointer by scripts/build_qucs.sh, and Ubuntu 24.04
# ships its libraries, Qt included, with frame pointers as well.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

[[ $# -ge 2 ]] || die "usage: $0 SCHEMATIC.sch LABEL [SAMPLES]"
schematic="$(realpath "$1")"
label="$2"
samples="${3:-20}"

[[ -x "$QUCS_S_BIN" ]] || die "$QUCS_S_BIN not found, run scripts/build_qucs.sh first"
[[ -f "$schematic" ]] || die "no such schematic: $schematic"
command -v perf >/dev/null || die "perf is not installed"

out_dir="$REPO_ROOT/results/profiles"
mkdir -p "$out_dir"
data="$out_dir/$label.perf.data"

echo ">> recording $label"
bench_exec perf record -q -o "$data" -F 999 --call-graph fp -- \
    "$QUCS_S_BIN" "--perf-bench=$schematic" "--perf-bench-repeat=$samples" \
    >/dev/null 2>&1

echo ">> folding stacks"
cd "$REPO_ROOT"
perf script -i "$data" --comm qucs-s -F comm,period,ip,sym,dso 2>/dev/null \
    | python3 -m bench.flamegraph fold > "$out_dir/$label.folded"
python3 -m bench.flamegraph render --title "$label" "$out_dir/$label.folded" \
    > "$out_dir/$label.svg"

echo ">> top frames by inclusive share"
python3 -m bench.flamegraph top --limit 15 "$out_dir/$label.folded"

echo "flame graph: $out_dir/$label.svg"
echo "open the recording with: hotspot $data"
