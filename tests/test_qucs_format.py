import pytest

from scenarios import qucs_format

R1 = '<R R1 1 200 260 -26 15 0 0 "1 kOhm" 1 "26.85" 0 "0.0" 0 "0.0" 0 "26.85" 0 "european" 0>'
W1 = '<230 260 270 260 "" 0 0 0 "">'


def test_sections_come_in_the_order_qucs_writes_them():
    text = qucs_format.render_schematic("grid_4", [R1], [W1])
    lines = text.splitlines()
    assert lines[0] == "<Qucs Schematic 26.1.1>"
    opening = [line for line in lines if line.startswith("<") and not line.startswith("</")
               and line.endswith(">") and " " not in line and "=" not in line]
    assert opening == ["<Properties>", "<Symbol>", "<Components>", "<Wires>",
                       "<Diagrams>", "<Paintings>"]
    assert text.endswith("</Paintings>\n")


def test_elements_are_indented_inside_their_section():
    lines = qucs_format.render_schematic("grid_4", [R1], [W1]).splitlines()
    components = lines.index("<Components>")
    assert lines[components + 1] == "  " + R1
    assert lines[components + 2] == "</Components>"
    wires = lines.index("<Wires>")
    assert lines[wires + 1] == "  " + W1


def test_dataset_names_follow_the_schematic_name():
    text = qucs_format.render_schematic("ladder_999", [], [])
    assert "  <DataSet=ladder_999.dat>" in text
    assert "  <DataDisplay=ladder_999.dpl>" in text
    assert "  <Script=ladder_999.m>" in text


def test_extent_goes_into_the_view_property():
    text = qucs_format.render_schematic("a", [], [], extent=(1234, 567))
    assert "  <View=0,0,1234,567,1,0,0>" in text


@pytest.mark.parametrize("name", ["", "has space", "a/b", "x=y", 'q"uote'])
def test_unusable_names_are_rejected(name):
    with pytest.raises(ValueError):
        qucs_format.render_schematic(name, [], [])


def test_lines_that_are_not_elements_are_rejected():
    with pytest.raises(ValueError):
        qucs_format.render_schematic("a", ["R R1 1 0 0"], [])


def test_write_uses_the_file_stem_as_name_and_creates_directories(tmp_path):
    path = qucs_format.write_schematic(tmp_path / "out" / "grid_4.sch", [R1], [W1])
    text = path.read_text(encoding="utf-8")
    assert "<DataSet=grid_4.dat>" in text
    assert text == qucs_format.render_schematic("grid_4", [R1], [W1])


def test_write_refuses_other_extensions(tmp_path):
    with pytest.raises(ValueError):
        qucs_format.write_schematic(tmp_path / "grid_4.txt", [], [])


def test_port_table_covers_every_model_with_properties():
    assert set(qucs_format.PORTS) == set(qucs_format.PROPERTIES)
    for ports in qucs_format.PORTS.values():
        for x, y in ports:
            assert x % qucs_format.GRID == 0 and y % qucs_format.GRID == 0


def test_text_sits_below_horizontal_and_beside_vertical_components():
    assert qucs_format.text_offset("R", 0) == (-26, 15)
    assert qucs_format.text_offset("R", 2) == (-26, 15)
    assert qucs_format.text_offset("C", 1) == (15, -26)
    assert qucs_format.text_offset("C", 3) == (15, -26)


def test_models_without_text_are_saved_with_a_zero_offset():
    assert qucs_format.text_offset("GND", 0) == (0, 0)
