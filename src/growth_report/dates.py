from __future__ import annotations

from datetime import date, timedelta


def previous_full_week(today: date | None = None) -> tuple[date, date]:
    anchor = today or date.today()
    monday_this_week = anchor - timedelta(days=anchor.weekday())
    week_start = monday_this_week - timedelta(days=7)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def report_id_for(week_start: date, week_end: date) -> str:
    return f"growth-{week_start.isoformat()}-{week_end.isoformat()}"

