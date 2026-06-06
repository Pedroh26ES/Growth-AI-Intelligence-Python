from __future__ import annotations

from pathlib import Path

from growth_report.models import ReportCollection


DEFAULT_REPORTS_PATH = Path("data/reports/weekly_reports.json")


def load_collection(path: Path = DEFAULT_REPORTS_PATH) -> ReportCollection:
    if not path.exists():
        return ReportCollection()
    return ReportCollection.model_validate_json(path.read_text(encoding="utf-8"))
