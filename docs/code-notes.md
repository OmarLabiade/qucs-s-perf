# Qucs-S code notes

Where the schematic view spends its time, from reading the source at the
pinned commit (`instrumentation/UPSTREAM_COMMIT`, version 26.1.1). Paths are
relative to the Qucs-S repository. These are observations about the code;
their measured cost is established separately.

## The view is painted by hand

`Schematic` (`qucs/schematic.h:111`) derives from `Q3ScrollView`, a port of
the Qt 3 scroll area kept in `qucs/qt3_compat/`. It is not a
`QGraphicsView`: there is no scene and no spatial index. The elements of a
document live in five `std::list` containers of pointers
(`qucs/schematic.h:277-286`): wires, nodes, diagrams, paintings, components.

A repaint follows this path:

    Q3ScrollView::viewportPaintEvent      qucs/qt3_compat/q3scrollview.cpp:1688
      Schematic::drawContents             qucs/schematic.cpp:422
        Schematic::drawGrid               qucs/schematic.cpp:1032
        Schematic::drawElements           qucs/schematic.cpp:451
          Component::paint                qucs/components/component.cpp:209
            Component::drawSymbol         qucs/components/component.cpp:249
          Wire::paint                     qucs/wire.cpp:89
          Node::paint                     qucs/node.cpp:35

`drawContents` receives the exposed rectangle and ignores it.
`drawElements` loops over every component, wire, node, diagram and painting
and paints each one, whether or not it is inside the viewport.
`Component::paint` draws the name and each visible property with
`QPainter::drawText`, which lays the text out again on every call.

## Loading looks up nodes by scanning

`Schematic::loadDocument` (`qucs/schematic_file.cpp:1183`) reads the file
section by section. Each component goes through `simpleInsertComponent`
(`:960`) and each wire through `simpleInsertWire` (`:1009`). Both call
`provideNode` for every port:

    Schematic::provideNode                qucs/schematic_element.cpp:343
      Schematic::findNode                 qucs/schematic_element.cpp:332   scans all nodes
      loop over all wires                 qucs/schematic_element.cpp:354   for each new node

So inserting element number k costs time proportional to k, and loading n
elements costs time proportional to n squared.

## Every edit serialises the document

`Schematic::setChanged(true, true)` (`qucs/schematic.cpp:240`) pushes an
undo state. The state is the whole document rendered to a string by
`createUndoString` (`qucs/schematic_file.cpp:1285`), which calls `save()` on
every component, wire, diagram and painting.

## Mouse moves repaint everything

While a selection rectangle is dragged, `MouseActions::MMoveSelect`
(`qucs/mouseactions.cpp:305`) posts a paint event for the rectangle on each
mouse move. The viewport is then repainted in full, through the path above.

## Upstream context

Performance changes have been accepted upstream before, for example
"Improve graph rendering performance" (#1042) and "Don't reload graph data
on every interaction" (#1600). No open or closed issue about repaint or
load time of large schematics was found when this study started.
