"""Folded stacks and flame graphs from `perf script` output.

Two steps, each usable on its own:

    perf script -i X.perf.data -F comm,period,ip,sym,dso \\
        | python -m bench.flamegraph fold > X.folded
    python -m bench.flamegraph render --title X X.folded > X.svg

The folded format is the usual one: `root;child;leaf weight`, one line per
distinct stack. It is plain text, diffs well, and is what gets committed
next to each SVG so that a figure can be rebuilt or queried later.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from dataclasses import dataclass, field
from html import escape
from typing import Iterable, TextIO

KERNEL_FRAME = "[kernel]"


def _frame_name(line: str) -> str:
    """Extracts the symbol from one `perf script` frame line.

    A frame line looks like `<address> <symbol> (<dso>)`. The symbol may
    itself contain spaces and parentheses (C++ signatures), so the dso is
    cut from the right and the address from the left.
    """
    text = line.strip()
    address, _, rest = text.partition(" ")
    symbol, _, dso = rest.rpartition(" (")
    dso = dso.rstrip(")")
    if not symbol:
        symbol = rest
    if dso in ("[kernel.kallsyms]", "[unknown]") and address.startswith("ffffffff"):
        return KERNEL_FRAME
    if symbol == "[unknown]":
        return f"[{dso.rsplit('/', 1)[-1]}]"
    # Drop the `+0x1f` offset perf adds to some symbols.
    return symbol.split("+0x", 1)[0]


def fold(lines: Iterable[str]) -> Counter[str]:
    """Folds `perf script -F comm,period,ip,sym,dso` output into stack counts.

    Samples are separated by blank lines. The first line of a sample holds
    the command name and the period; the following lines are frames, leaf
    first. Consecutive kernel frames collapse into one `[kernel]` frame.
    """
    folded: Counter[str] = Counter()
    command = ""
    weight = 0
    frames: list[str] = []

    def flush() -> None:
        if command:
            stack = [command, *reversed(frames)]
            folded[";".join(stack)] += weight

    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            flush()
            command, weight, frames = "", 0, []
        elif not line[0].isspace():
            head = line.split()
            command = head[0]
            weight = int(head[-1]) if head[-1].isdigit() else 1
        else:
            name = _frame_name(line)
            if name == KERNEL_FRAME and frames and frames[-1] == KERNEL_FRAME:
                continue
            frames.append(name)
    flush()
    return folded


def read_folded(lines: Iterable[str]) -> Counter[str]:
    folded: Counter[str] = Counter()
    for line in lines:
        stack, _, weight = line.rstrip("\n").rpartition(" ")
        if stack:
            folded[stack] += int(weight)
    return folded


def write_folded(folded: Counter[str], out: TextIO) -> None:
    for stack in sorted(folded):
        out.write(f"{stack} {folded[stack]}\n")


def inclusive_shares(folded: Counter[str]) -> dict[str, float]:
    """Share of all samples in which each frame appears anywhere in the stack."""
    total = sum(folded.values())
    counts: Counter[str] = Counter()
    for stack, weight in folded.items():
        for frame in set(stack.split(";")):
            counts[frame] += weight
    return {frame: count / total for frame, count in counts.items()} if total else {}


@dataclass
class _Node:
    name: str
    weight: int = 0
    children: dict[str, "_Node"] = field(default_factory=dict)


def _build_tree(folded: Counter[str]) -> _Node:
    root = _Node("all")
    for stack, weight in folded.items():
        node = root
        node.weight += weight
        for name in stack.split(";"):
            node = node.children.setdefault(name, _Node(name))
            node.weight += weight
    return root


def _colour(name: str) -> str:
    """A stable warm colour per frame name, so two graphs can be compared."""
    digest = hashlib.sha1(name.encode()).digest()
    red = 205 + digest[0] % 50
    green = 80 + digest[1] % 130
    blue = digest[2] % 55
    return f"rgb({red},{green},{blue})"


def render_svg(folded: Counter[str], title: str, width: int = 1600,
               min_share: float = 0.001) -> str:
    """Renders an SVG flame graph, root at the bottom.

    Frames narrower than `min_share` of the total are left out. Every
    rectangle carries a tooltip with the full name, sample share and count.
    """
    root = _build_tree(folded)
    total = root.weight
    row_height = 17
    margin = 10
    header = 40
    rows: list[tuple[int, float, float, _Node]] = []

    def place(node: _Node, depth: int, left: float) -> None:
        share = node.weight / total if total else 0.0
        if share < min_share:
            return
        rows.append((depth, left, share, node))
        offset = left
        for child in sorted(node.children.values(), key=lambda n: n.name):
            place(child, depth + 1, offset)
            offset += child.weight / total

    if total:
        place(root, 0, 0.0)

    depth_count = max((depth for depth, *_ in rows), default=0) + 1
    height = header + depth_count * row_height + margin
    usable = width - 2 * margin
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="monospace" font-size="11">',
        f'<rect width="{width}" height="{height}" fill="#fdfdf6"/>',
        f'<text x="{width / 2:.0f}" y="24" text-anchor="middle" font-size="15">'
        f"{escape(title)}</text>",
    ]
    for depth, left, share, node in rows:
        x = margin + left * usable
        y = height - margin - (depth + 1) * row_height
        w = share * usable
        tooltip = f"{node.name} ({share * 100:.2f}%, {node.weight} samples)"
        parts.append(
            f'<g><title>{escape(tooltip)}</title>'
            f'<rect x="{x:.2f}" y="{y}" width="{max(w - 0.5, 0.5):.2f}" '
            f'height="{row_height - 1}" fill="{_colour(node.name)}" rx="1"/>'
        )
        visible_chars = int(w / 6.6) - 1
        if visible_chars >= 3:
            label = node.name
            if len(label) > visible_chars:
                label = label[: visible_chars - 2] + ".."
            parts.append(f'<text x="{x + 3:.2f}" y="{y + 12}">{escape(label)}</text>')
        parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("fold", help="perf script output on stdin, folded stacks on stdout")

    render = commands.add_parser("render", help="folded stacks file to SVG on stdout")
    render.add_argument("folded")
    render.add_argument("--title", default="flame graph")
    render.add_argument("--width", type=int, default=1600)

    top = commands.add_parser("top", help="frames ranked by inclusive share")
    top.add_argument("folded")
    top.add_argument("--limit", type=int, default=30)

    args = parser.parse_args(argv)
    if args.command == "fold":
        write_folded(fold(sys.stdin), sys.stdout)
    elif args.command == "render":
        with open(args.folded, encoding="utf-8") as handle:
            sys.stdout.write(render_svg(read_folded(handle), args.title, args.width))
    else:
        with open(args.folded, encoding="utf-8") as handle:
            shares = inclusive_shares(read_folded(handle))
        ranked = sorted(shares.items(), key=lambda item: -item[1])[: args.limit]
        for frame, share in ranked:
            print(f"{share * 100:6.2f}%  {frame}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
