#ifndef MICROBENCH_STATS_H
#define MICROBENCH_STATS_H

#include <vector>

namespace microbench {

// Summary of a series of timings. All values are in the unit of the input.
struct Summary {
    int count = 0;
    double min = 0.0;
    double median = 0.0;
    double p95 = 0.0;
    double max = 0.0;
    double mean = 0.0;
};

// Quantile with linear interpolation between the two nearest ranks
// (the default method of numpy.percentile). `q` is in [0, 1].
// Returns 0 for an empty input.
double quantile(std::vector<double> samples, double q);

Summary summarize(const std::vector<double>& samples);

} // namespace microbench

#endif
