from datetime import date, datetime, timezone

from growth_report.models import WeeklyGrowthReport
from growth_report.services.storage import JsonReportStore


def test_store_replaces_report_with_same_id(tmp_path) -> None:
    store = JsonReportStore(tmp_path / "reports.json")
    first = _report("same-id", "First")
    second = _report("same-id", "Second")

    store.save_report(first)
    store.save_report(second)

    collection = store.load()
    assert len(collection.reports) == 1
    assert collection.reports[0].executive_summary == "Second"


def _report(report_id: str, summary: str) -> WeeklyGrowthReport:
    return WeeklyGrowthReport(
        report_id=report_id,
        week_start=date(2026, 6, 1),
        week_end=date(2026, 6, 7),
        generated_at=datetime.now(timezone.utc),
        executive_summary=summary,
        intro="Intro",
        performance="Performance",
        risks=[],
        rates=[],
        opportunities=[],
        recommendations=[],
        channels=[],
        campaigns=[],
        conclusion="Conclusion",
        sources=[],
        confidence_notes=[],
    )

