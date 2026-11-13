# Results

Everything in this directory comes from a run on the machine described in
[docs/method.md](../docs/method.md). Nothing here is edited by hand.

| Path | Content |
|---|---|
| `profiles/NAME.folded` | folded call stacks from `perf record`, one line per distinct stack |
| `profiles/NAME.svg` | flame graph rendered from the folded stacks |

Raw `perf.data` recordings are not committed (they are large and tied to
the local binary). The folded stacks keep the information a figure was
built from: `python3 -m bench.flamegraph top profiles/NAME.folded` ranks
the frames again, and `render` rebuilds the SVG.

Timing tables and before/after comparisons are added here as the baseline
and each change are measured.
