#include "options.h"
#include "report.h"
#include "stats.h"

#include <QJsonArray>
#include <QJsonDocument>
#include <QTemporaryDir>
#include <QTest>

using namespace microbench;

class TestSupport : public QObject {
    Q_OBJECT

private slots:
    void quantileInterpolatesBetweenRanks()
    {
        const std::vector<double> samples{4.0, 1.0, 3.0, 2.0};
        QCOMPARE(quantile(samples, 0.0), 1.0);
        QCOMPARE(quantile(samples, 0.5), 2.5);
        QCOMPARE(quantile(samples, 1.0), 4.0);
        QCOMPARE(quantile({10.0, 20.0}, 0.25), 12.5);
    }

    void quantileOfEmptyInputIsZero()
    {
        QCOMPARE(quantile({}, 0.5), 0.0);
    }

    void summaryOfOddAndEvenCounts()
    {
        const Summary odd = summarize({3.0, 1.0, 2.0});
        QCOMPARE(odd.count, 3);
        QCOMPARE(odd.min, 1.0);
        QCOMPARE(odd.median, 2.0);
        QCOMPARE(odd.max, 3.0);
        QCOMPARE(odd.mean, 2.0);

        const Summary even = summarize({1.0, 2.0, 3.0, 10.0});
        QCOMPARE(even.median, 2.5);
        QCOMPARE(even.mean, 4.0);
    }

    void summaryIsRobustToOneOutlier()
    {
        std::vector<double> samples(99, 5.0);
        samples.push_back(500.0);
        const Summary summary = summarize(samples);
        QCOMPARE(summary.median, 5.0);
        QCOMPARE(summary.max, 500.0);
        QVERIFY(summary.mean > 9.0);
    }

    void defaultsWhenNoArguments()
    {
        const ParseResult parsed = parseOptions({});
        QVERIFY(parsed.ok());
        QVERIFY(parsed.options.backend == Backend::PaintAll);
        QCOMPARE(parsed.options.items, 1000);
        QCOMPARE(parsed.options.frames, 50);
        QCOMPARE(parsed.options.scale, 1.0);
        QCOMPARE(parsed.options.viewport, QSize(1280, 800));
        QVERIFY(parsed.options.jsonPath.isEmpty());
    }

    void allOptionsAreRead()
    {
        const ParseResult parsed = parseOptions({"--backend", "graphicsview", "--items", "20000",
                                                 "--frames=5", "--scale", "0", "--viewport",
                                                 "933x667", "--json", "out.json"});
        QVERIFY2(parsed.ok(), qPrintable(parsed.error));
        QVERIFY(parsed.options.backend == Backend::GraphicsView);
        QCOMPARE(parsed.options.items, 20000);
        QCOMPARE(parsed.options.frames, 5);
        QCOMPARE(parsed.options.scale, 0.0);
        QCOMPARE(parsed.options.viewport, QSize(933, 667));
        QCOMPARE(parsed.options.jsonPath, QString("out.json"));
    }

    void invalidArgumentsAreReported_data()
    {
        QTest::addColumn<QStringList>("arguments");
        QTest::newRow("unknown backend") << QStringList{"--backend", "opengl"};
        QTest::newRow("zero items") << QStringList{"--items", "0"};
        QTest::newRow("non numeric frames") << QStringList{"--frames", "many"};
        QTest::newRow("negative scale") << QStringList{"--scale", "-1"};
        QTest::newRow("bad viewport") << QStringList{"--viewport", "1280"};
        QTest::newRow("unknown option") << QStringList{"--threads", "4"};
        QTest::newRow("positional argument") << QStringList{"extra"};
    }

    void invalidArgumentsAreReported()
    {
        QFETCH(QStringList, arguments);
        const ParseResult parsed = parseOptions(arguments);
        QVERIFY(!parsed.ok());
        QVERIFY(!parsed.error.isEmpty());
    }

    void backendNamesRoundTrip()
    {
        for (const Backend backend :
             {Backend::PaintAll, Backend::PaintVisible, Backend::GraphicsView}) {
            QVERIFY(backendFromString(backendName(backend)) == backend);
        }
        QVERIFY(!backendFromString("nonsense").has_value());
    }

    void reportKeepsParametersSamplesAndSummary()
    {
        Options options;
        options.backend = Backend::PaintVisible;
        options.items = 4;
        RunResult result;
        result.frameMs = {2.0, 4.0, 6.0};
        result.visibleItems = 3;

        const QJsonObject report = toJson(options, result);
        QCOMPARE(report["backend"].toString(), QString("paint-visible"));
        QCOMPARE(report["items"].toInt(), 4);
        QCOMPARE(report["visible_items"].toInt(), 3);
        QCOMPARE(report["frames"].toInt(), 3);
        QCOMPARE(report["frame_ms"].toArray().size(), 3);
        QCOMPARE(report["median_ms"].toDouble(), 4.0);
        QCOMPARE(report["min_ms"].toDouble(), 2.0);
        QCOMPARE(report["max_ms"].toDouble(), 6.0);
    }

    void reportIsWrittenAsOneJsonLine()
    {
        QTemporaryDir directory;
        QVERIFY(directory.isValid());
        const QString path = directory.filePath("report.json");

        QVERIFY(writeReport(toJson(Options{}, RunResult{}), path));

        QFile file(path);
        QVERIFY(file.open(QIODevice::ReadOnly));
        const QByteArray content = file.readAll();
        QCOMPARE(content.count('\n'), 1);
        QVERIFY(QJsonDocument::fromJson(content).isObject());
    }

    void unwritablePathIsAnError()
    {
        QString error;
        QVERIFY(!writeReport(QJsonObject{}, "/nonexistent-directory/report.json", &error));
        QVERIFY(error.contains("report.json"));
    }
};

QTEST_APPLESS_MAIN(TestSupport)
#include "test_support.moc"
