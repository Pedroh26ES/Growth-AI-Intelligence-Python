from datetime import date

from growth_report.dates import previous_full_week, report_id_for


def test_previous_full_week_from_monday() -> None:
    week_start, week_end = previous_full_week(date(2026, 6, 8))

    assert week_start == date(2026, 6, 1)
    assert week_end == date(2026, 6, 7)


def test_report_id_for() -> None:
    assert (
        report_id_for(date(2026, 6, 1), date(2026, 6, 7))
        == "growth-2026-06-01-2026-06-07"
    )

