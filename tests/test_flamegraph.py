from collections import Counter

from bench import flamegraph

PERF_SCRIPT = """\
qucs-s     1000
\t    55d0aa001000 Component::paint(QPainter*) (/b/qucs/qucs-s)
\t    55d0aa002000 Schematic::drawElements(QPainter*) (/b/qucs/qucs-s)
\t    55d0aa003000 main (/b/qucs/qucs-s)

qucs-s     1000
\t    55d0aa001000 Component::paint(QPainter*) (/b/qucs/qucs-s)
\t    55d0aa002000 Schematic::drawElements(QPainter*) (/b/qucs/qucs-s)
\t    55d0aa003000 main (/b/qucs/qucs-s)

qucs-s     500
\tffffffffb161b00d [unknown] ([unknown])
\tffffffffb16399c5 [unknown] ([unknown])
\t    7cca75cd1d2c mmap64+0x1c (/usr/lib/x86_64-linux-gnu/libc.so.6)
\t    7cca75000000 [unknown] (/usr/lib/x86_64-linux-gnu/libQt6Gui.so.6.4.2)
\t    55d0aa003000 main (/b/qucs/qucs-s)
"""


def test_fold_puts_the_root_first_and_sums_identical_stacks():
    folded = flamegraph.fold(PERF_SCRIPT.splitlines(keepends=True))
    paint = "qucs-s;main;Schematic::drawElements(QPainter*);Component::paint(QPainter*)"
    assert folded[paint] == 2000


def test_fold_collapses_kernel_frames_and_names_unknown_frames_by_library():
    folded = flamegraph.fold(PERF_SCRIPT.splitlines(keepends=True))
    assert folded["qucs-s;main;[libQt6Gui.so.6.4.2];mmap64;[kernel]"] == 500
    assert len(folded) == 2


def test_fold_handles_a_missing_trailing_blank_line():
    folded = flamegraph.fold(["qucs-s 7\n", "\t 1234 main (/b/qucs-s)\n"])
    assert folded == Counter({"qucs-s;main": 7})


def test_folded_text_round_trips(tmp_path):
    folded = Counter({"a;b;c": 3, "a;b": 1, "a;with space(int, int)": 2})
    path = tmp_path / "x.folded"
    with open(path, "w", encoding="utf-8") as handle:
        flamegraph.write_folded(folded, handle)
    with open(path, encoding="utf-8") as handle:
        assert flamegraph.read_folded(handle) == folded


def test_inclusive_share_counts_a_recursive_frame_once_per_sample():
    shares = flamegraph.inclusive_shares(Counter({"a;b;b": 1, "a;c": 3}))
    assert shares["a"] == 1.0
    assert shares["b"] == 0.25
    assert shares["c"] == 0.75


def test_svg_has_one_tooltip_per_frame_and_escapes_names():
    svg = flamegraph.render_svg(Counter({"main;f<int>(a&)": 3, "main;g": 1}), "t & t")
    assert svg.startswith("<svg")
    assert svg.count("<title>") == 4  # all, main, f, g
    assert "f&lt;int&gt;(a&amp;) (75.00%, 3 samples)" in svg
    assert "t &amp; t" in svg


def test_svg_drops_frames_below_the_minimum_share():
    folded = Counter({"main;big": 9999, "main;tiny": 1})
    svg = flamegraph.render_svg(folded, "t", min_share=0.001)
    assert "big" in svg
    assert "tiny" not in svg


def test_empty_input_still_gives_a_valid_svg():
    svg = flamegraph.render_svg(Counter(), "empty")
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
