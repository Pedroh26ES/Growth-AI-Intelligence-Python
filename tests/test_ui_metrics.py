from datetime import date, datetime, timezone

from growth_report.models import ChannelInsight, ChannelStatus, RateMetric, ReportCollection, WeeklyGrowthReport
from growth_report.ui.metrics import channel_comparisons, previous_report, rate_label


def test_channel_comparisons_use_immediate_previous_report_by_week() -> None:
    oldest = _report("oldest", date(2026, 5, 11), 1000)
    previous = _report("previous", date(2026, 5, 25), 2000)
    current = _report("current", date(2026, 6, 1), 1500)
    collection = ReportCollection(reports=[current, oldest, previous])

    comparison = channel_comparisons(current, collection)[0]

    assert previous_report(current, collection) == previous
    assert comparison["previous"] == 2000
    assert comparison["previous_week"] == "25/05/2026 - 31/05/2026"
    assert comparison["change_pct"] == -25.0


def test_channel_comparisons_handle_first_report_without_previous_week() -> None:
    current = _report("current", date(2026, 6, 1), 1500)

    comparison = channel_comparisons(current, ReportCollection(reports=[current]))[0]

    assert comparison["previous"] is None
    assert comparison["previous_week"] is None
    assert comparison["change_pct"] is None
    assert comparison["status"] == "sem histórico"


def test_rate_label_accepts_portuguese_metric_names() -> None:
    report = _report("current", date(2026, 6, 1), 1500)
    report.rates = [RateMetric(name="Crescimento de Receita", value=12.4)]

    assert rate_label(report, "Revenue Growth") == "+12.4%"


def _report(report_id: str, week_start: date, channel_revenue: float) -> WeeklyGrowthReport:
    week_end = date.fromordinal(week_start.toordinal() + 6)
    return WeeklyGrowthReport(
        report_id=report_id,
        week_start=week_start,
        week_end=week_end,
        generated_at=datetime.now(timezone.utc),
        executive_summary="Resumo",
        intro="Intro",
        performance="Performance",
        risks=[],
        rates=[],
        opportunities=[],
        recommendations=[],
        channels=[
            ChannelInsight(
                channel="Paid Search",
                status=ChannelStatus.UP,
                current_value=channel_revenue,
                summary="Resumo do canal",
            )
        ],
        campaigns=[],
        conclusion="Conclusão",
        sources=[],
        confidence_notes=[],
    )
