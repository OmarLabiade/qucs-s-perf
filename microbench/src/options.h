#ifndef MICROBENCH_OPTIONS_H
#define MICROBENCH_OPTIONS_H

#include <QSize>
#include <QString>
#include <QStringList>

#include <optional>

namespace microbench {

// How the items are put on screen.
enum class Backend {
    // One widget, one loop: paint every item on every repaint.
    // This is what Qucs-S does in Schematic::drawElements.
    PaintAll,
    // Same widget, but items outside the visible area are skipped.
    PaintVisible,
    // QGraphicsView over a QGraphicsScene, which indexes its items.
    GraphicsView,
};

QString backendName(Backend backend);
std::optional<Backend> backendFromString(const QString& name);

struct Options {
    Backend backend = Backend::PaintAll;
    int items = 1000;
    int frames = 50;
    // 1.0 shows the items at their natural size, so only part of a large
    // set is visible. 0 means "fit everything into the viewport".
    double scale = 1.0;
    QSize viewport = QSize(1280, 800);
    // Empty: the report goes to stdout.
    QString jsonPath;
};

struct ParseResult {
    Options options;
    // Non-empty when the arguments are invalid.
    QString error;

    bool ok() const { return error.isEmpty(); }
};

// Parses the command line (without the program name).
// Never exits the process, so it can be tested.
ParseResult parseOptions(const QStringList& arguments);

QString usage();

} // namespace microbench

#endif
