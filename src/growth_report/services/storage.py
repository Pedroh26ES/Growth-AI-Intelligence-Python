from __future__ import annotations

import json
from pathlib import Path

from growth_report.models import ReportCollection, WeeklyGrowthReport


class JsonReportStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> ReportCollection:
        if not self.path.exists():
            return ReportCollection()

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            payload = {"reports": payload}
        return ReportCollection.model_validate(payload)

    def save_report(self, report: WeeklyGrowthReport) -> None:
        collection = self.load()
        reports_by_id = {existing.report_id: existing for existing in collection.reports}
        reports_by_id[report.report_id] = report
        ordered_reports = sorted(
            reports_by_id.values(),
            key=lambda item: item.week_start,
            reverse=True,
        )

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            ReportCollection(reports=ordered_reports).model_dump_json(indent=2),
            encoding="utf-8",
        )

