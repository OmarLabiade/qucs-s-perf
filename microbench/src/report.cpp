#include "report.h"

#include "stats.h"

#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>

#include <cstdio>

namespace microbench {

QJsonObject toJson(const Options& options, const RunResult& result)
{
    QJsonArray samples;
    for (const double ms : result.frameMs) {
        samples.append(ms);
    }

    const Summary summary = summarize(result.frameMs);

    QJsonObject report;
    report["schema"] = 1;
    report["backend"] = backendName(options.backend);
    report["items"] = options.items;
    report["visible_items"] = result.visibleItems;
    report["scale"] = options.scale;
    report["viewport_w"] = options.viewport.width();
    report["viewport_h"] = options.viewport.height();
    report["qt_version"] = QString::fromLatin1(qVersion());
    report["frames"] = summary.count;
    report["frame_ms"] = samples;
    report["min_ms"] = summary.min;
    report["median_ms"] = summary.median;
    report["p95_ms"] = summary.p95;
    report["max_ms"] = summary.max;
    report["mean_ms"] = summary.mean;
    return report;
}

bool writeReport(const QJsonObject& report, const QString& path, QString* error)
{
    const QByteArray line = QJsonDocument(report).toJson(QJsonDocument::Compact) + '\n';

    if (path.isEmpty()) {
        std::fwrite(line.constData(), 1, static_cast<std::size_t>(line.size()), stdout);
        std::fflush(stdout);
        return true;
    }

    QFile file(path);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Truncate) || file.write(line) != line.size()) {
        if (error != nullptr) {
            *error = QStringLiteral("cannot write %1: %2").arg(path, file.errorString());
        }
        return false;
    }
    return true;
}

} // namespace microbench
