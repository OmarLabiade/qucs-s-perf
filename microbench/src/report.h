#ifndef MICROBENCH_REPORT_H
#define MICROBENCH_REPORT_H

#include "options.h"

#include <QJsonObject>
#include <QString>

#include <vector>

namespace microbench {

// What one benchmark run produced.
struct RunResult {
    // Duration of each timed repaint, in milliseconds.
    std::vector<double> frameMs;
    // Items intersecting the visible area during the run.
    int visibleItems = 0;
};

// Report with the run parameters, the raw samples and their summary.
// The raw samples stay in the report: a median alone cannot be re-analysed.
QJsonObject toJson(const Options& options, const RunResult& result);

// Writes the report as one line of JSON to `path`, or to stdout when
// `path` is empty. Returns false and sets `error` if the file cannot be
// written.
bool writeReport(const QJsonObject& report, const QString& path, QString* error = nullptr);

} // namespace microbench

#endif
