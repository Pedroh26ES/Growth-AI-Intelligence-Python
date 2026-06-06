import pandas as pd

from growth_report.collectors.extractors import extract_excel_summary
from growth_report.collectors.factory import _google_sheets_export_url


def test_extract_excel_summary_reads_workbook(tmp_path) -> None:
    path = tmp_path / "growth.xlsx"
    pd.DataFrame(
        [
            {"channel": "Paid Search", "revenue": 1200, "conversions": 30},
            {"channel": "Email", "revenue": 800, "conversions": 20},
        ]
    ).to_excel(path, index=False, sheet_name="growth")

    summary = extract_excel_summary(path)

    assert "Excel sheet: growth preview" in summary
    assert "Paid Search" in summary
    assert "revenue" in summary


def test_google_sheets_url_is_converted_to_csv_export() -> None:
    url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=456"

    export_url = _google_sheets_export_url(url)

    assert export_url == "https://docs.google.com/spreadsheets/d/abc123/export?format=csv&gid=456"
