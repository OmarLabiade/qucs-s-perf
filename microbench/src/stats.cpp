#include "stats.h"

#include <algorithm>
#include <cmath>
#include <numeric>

namespace microbench {

double quantile(std::vector<double> samples, double q)
{
    if (samples.empty()) {
        return 0.0;
    }
    std::sort(samples.begin(), samples.end());
    const double position = std::clamp(q, 0.0, 1.0) * static_cast<double>(samples.size() - 1);
    const auto lower = static_cast<std::size_t>(std::floor(position));
    const auto upper = static_cast<std::size_t>(std::ceil(position));
    const double fraction = position - static_cast<double>(lower);
    return samples[lower] + (samples[upper] - samples[lower]) * fraction;
}

Summary summarize(const std::vector<double>& samples)
{
    Summary summary;
    if (samples.empty()) {
        return summary;
    }
    summary.count = static_cast<int>(samples.size());
    const auto [min, max] = std::minmax_element(samples.begin(), samples.end());
    summary.min = *min;
    summary.max = *max;
    summary.median = quantile(samples, 0.5);
    summary.p95 = quantile(samples, 0.95);
    summary.mean = std::accumulate(samples.begin(), samples.end(), 0.0)
                   / static_cast<double>(samples.size());
    return summary;
}

} // namespace microbench
