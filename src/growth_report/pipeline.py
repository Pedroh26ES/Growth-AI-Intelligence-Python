from __future__ import annotations

from datetime import date
from pathlib import Path

from growth_report.collectors import collect_sources
from growth_report.config import AppConfig, resolve_project_path
from growth_report.dates import previous_full_week
from growth_report.models import WeeklyGrowthReport
from growth_report.services.report_generator_factory import build_report_generator
from growth_report.services.storage import JsonReportStore


def run_pipeline(
    config: AppConfig,
    *,
    dry_run: bool = False,
    today: date | None = None,
) -> WeeklyGrowthReport:
    raw_dir = resolve_project_path(config.storage.raw_dir)
    reports_path = resolve_project_path(config.storage.reports_path)

    week_start, week_end = previous_full_week(today)
    documents = collect_sources(config.sources, raw_dir)

    generator = build_report_generator(config.ai, dry_run=dry_run)
    report = generator.generate(documents, week_start, week_end)

    store = JsonReportStore(Path(reports_path))
    store.save_report(report)
    return report
