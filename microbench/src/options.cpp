#include "options.h"

#include <QCommandLineParser>

namespace microbench {

namespace {

struct BackendName {
    Backend backend;
    const char* name;
};

constexpr BackendName backendNames[] = {
    {Backend::PaintAll, "paint-all"},
    {Backend::PaintVisible, "paint-visible"},
    {Backend::GraphicsView, "graphicsview"},
};

void addOptions(QCommandLineParser& parser)
{
    parser.addOptions({
        {"backend", "paint-all, paint-visible or graphicsview (default paint-all)", "NAME"},
        {"items", "number of items to draw (default 1000)", "N"},
        {"frames", "number of timed repaints (default 50)", "N"},
        {"scale", "zoom factor, 0 fits all items in the viewport (default 1.0)", "FACTOR"},
        {"viewport", "viewport size in pixels (default 1280x800)", "WxH"},
        {"json", "write the report to FILE instead of stdout", "FILE"},
    });
}

// Reads a strictly positive integer option, keeping `value` when unset.
bool readCount(const QCommandLineParser& parser, const QString& name, int& value, QString& error)
{
    if (!parser.isSet(name)) {
        return true;
    }
    bool ok = false;
    const int parsed = parser.value(name).toInt(&ok);
    if (!ok || parsed <= 0) {
        error = QStringLiteral("--%1 expects a positive integer, got '%2'")
                    .arg(name, parser.value(name));
        return false;
    }
    value = parsed;
    return true;
}

} // namespace

QString backendName(Backend backend)
{
    for (const auto& entry : backendNames) {
        if (entry.backend == backend) {
            return QString::fromLatin1(entry.name);
        }
    }
    return {};
}

std::optional<Backend> backendFromString(const QString& name)
{
    for (const auto& entry : backendNames) {
        if (name == QLatin1String(entry.name)) {
            return entry.backend;
        }
    }
    return std::nullopt;
}

ParseResult parseOptions(const QStringList& arguments)
{
    ParseResult result;
    QCommandLineParser parser;
    addOptions(parser);

    // QCommandLineParser expects the program name as the first element.
    if (!parser.parse(QStringList{QStringLiteral("microbench")} + arguments)) {
        result.error = parser.errorText();
        return result;
    }
    if (!parser.positionalArguments().isEmpty()) {
        result.error = QStringLiteral("unexpected argument '%1'")
                           .arg(parser.positionalArguments().constFirst());
        return result;
    }

    Options& options = result.options;

    if (parser.isSet("backend")) {
        const auto backend = backendFromString(parser.value("backend"));
        if (!backend) {
            result.error = QStringLiteral("unknown backend '%1'").arg(parser.value("backend"));
            return result;
        }
        options.backend = *backend;
    }

    if (!readCount(parser, "items", options.items, result.error)
        || !readCount(parser, "frames", options.frames, result.error)) {
        return result;
    }

    if (parser.isSet("scale")) {
        bool ok = false;
        const double scale = parser.value("scale").toDouble(&ok);
        if (!ok || scale < 0.0) {
            result.error = QStringLiteral("--scale expects a number >= 0, got '%1'")
                               .arg(parser.value("scale"));
            return result;
        }
        options.scale = scale;
    }

    if (parser.isSet("viewport")) {
        const QStringList parts = parser.value("viewport").split('x');
        bool widthOk = false;
        bool heightOk = false;
        const int width = parts.value(0).toInt(&widthOk);
        const int height = parts.value(1).toInt(&heightOk);
        if (parts.size() != 2 || !widthOk || !heightOk || width <= 0 || height <= 0) {
            result.error = QStringLiteral("--viewport expects WxH, got '%1'")
                               .arg(parser.value("viewport"));
            return result;
        }
        options.viewport = QSize(width, height);
    }

    options.jsonPath = parser.value("json");
    return result;
}

QString usage()
{
    QCommandLineParser parser;
    parser.setApplicationDescription(
        "Draws N items with one of several strategies and times each repaint.");
    addOptions(parser);
    return parser.helpText();
}

} // namespace microbench
