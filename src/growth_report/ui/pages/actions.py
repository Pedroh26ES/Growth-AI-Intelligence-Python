from __future__ import annotations

from growth_report.models import WeeklyGrowthReport


def render(report: WeeklyGrowthReport, ui) -> None:
    ui.roas_benchmark_note()
    ui.action_board(report)
    ui.opportunities(report)
