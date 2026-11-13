"""Facts about the Qucs-S schematic file format (version 26.1.1).

A `.sch` file is plain text. After a header line come six sections, each
opened by `<Name>` and closed by `</Name>`, holding one element per line:

    <Qucs Schematic 26.1.1>
    <Properties> ... </Properties>
    <Symbol> ... </Symbol>
    <Components>
      <R R1 1 200 260 -26 15 0 0 "1 kOhm" 1 "26.85" 0 ...>
    </Components>
    <Wires>
      <230 260 270 260 "" 0 0 0 "">
    </Wires>
    <Diagrams> ... </Diagrams>
    <Paintings> ... </Paintings>

A component line is

    <Model Name active x y text_x text_y mirror rotation properties...>

where (x, y) is the component centre, `rotation` counts quarter turns
counter-clockwise, and each property is a quoted value followed by a 0/1
"show on schematic" flag. The parser is `Component::load` in
qucs/components/component.cpp.

A wire line is

    <x1 y1 x2 y2 "label" label_x label_y label_distance "node set">

parsed by `Wire::load` in qucs/wire.cpp. Wires are horizontal or vertical.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

FORMAT_VERSION = "26.1.1"

# Everything in a schematic sits on this grid, in schematic units.
GRID = 10

# Port positions relative to the component centre at rotation 0.
# From the component constructors, e.g. qucs/components/resistor.cpp.
PORTS: dict[str, tuple[tuple[int, int], ...]] = {
    "R": ((-30, 0), (30, 0)),
    "C": ((-30, 0), (30, 0)),
    "GND": ((0, 0),),
}

# Property list of each model as it appears in a saved file, default values.
PROPERTIES: dict[str, str] = {
    "R": '"1 kOhm" 1 "26.85" 0 "0.0" 0 "0.0" 0 "26.85" 0 "european" 0',
    "C": '"1 nF" 1 "" 0 "neutral" 0',
    "GND": "",
}


# Name written for components that have none, such as ground symbols.
UNNAMED = "*"


def text_offset(model: str, rotation: int) -> tuple[int, int]:
    """Position of the name and value text relative to the component centre.

    Below a horizontal component, to the right of a vertical one. Models
    without properties and without a name, such as ground, have no text and
    are saved with (0, 0).
    """
    if not PROPERTIES[model]:
        return (0, 0)
    return (15, -26) if rotation % 2 else (-26, 15)


def render_schematic(name: str, component_lines: Iterable[str],
                     wire_lines: Iterable[str],
                     extent: tuple[int, int] = (800, 600)) -> str:
    """Text of a complete schematic file.

    `name` is the file name without extension. It is written into the
    DataSet, DataDisplay and Script properties: when these do not match the
    file name, Qucs-S opens a dialog on load and asks whether to fix them.

    `component_lines` and `wire_lines` are complete lines without
    indentation, e.g. `<230 260 270 260 "" 0 0 0 "">`. `extent` is the
    width and height of the drawing; Qucs-S recomputes the view on load.
    """
    if not name or any(c in name for c in '/\\<>"= '):
        raise ValueError(f"not usable as a schematic name: {name!r}")

    def section(tag: str, lines: Iterable[str] = ()) -> list[str]:
        body = []
        for line in lines:
            if not (line.startswith("<") and line.endswith(">")):
                raise ValueError(f"not an element line: {line!r}")
            body.append(f"  {line}")
        return [f"<{tag}>", *body, f"</{tag}>"]

    width, height = extent
    properties = [
        f"<View=0,0,{width},{height},1,0,0>",
        f"<Grid={GRID},{GRID},1>",
        f"<DataSet={name}.dat>",
        f"<DataDisplay={name}.dpl>",
        "<OpenDisplay=0>",
        f"<Script={name}.m>",
        "<RunScript=0>",
        "<showFrame=0>",
        "<FrameText0=Title>",
        "<FrameText1=Drawn By:>",
        "<FrameText2=Date:>",
        "<FrameText3=Revision:>",
    ]
    lines = [
        f"<Qucs Schematic {FORMAT_VERSION}>",
        *section("Properties", properties),
        *section("Symbol"),
        *section("Components", component_lines),
        *section("Wires", wire_lines),
        *section("Diagrams"),
        *section("Paintings"),
    ]
    return "\n".join(lines) + "\n"


def write_schematic(path: Path, component_lines: Iterable[str],
                    wire_lines: Iterable[str],
                    extent: tuple[int, int] = (800, 600)) -> Path:
    """Writes a schematic to `path`; the file stem becomes its name."""
    path = Path(path)
    if path.suffix != ".sch":
        raise ValueError(f"schematic files end in .sch: {path}")
    text = render_schematic(path.stem, component_lines, wire_lines, extent)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
