from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from pypdf import PdfReader


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(page.strip() for page in pages if page.strip())


def extract_csv_summary(path: Path) -> str:
    dataframe = pd.read_csv(path)
    return _summarize_dataframe(dataframe, "CSV")


def extract_excel_summary(path: Path) -> str:
    workbook = pd.ExcelFile(path)
    sections = []
    for sheet_name in workbook.sheet_names:
        dataframe = workbook.parse(sheet_name)
        sections.append(_summarize_dataframe(dataframe, f"Excel sheet: {sheet_name}"))
    return "\n\n".join(sections)


def _summarize_dataframe(dataframe: pd.DataFrame, label: str) -> str:
    buffer = StringIO()
    dataframe.info(buf=buffer)

    preview = dataframe.head(20).to_string(index=False)
    numeric_summary = dataframe.describe(include="all").fillna("").to_string()

    return (
        f"{label} columns and types:\n{buffer.getvalue()}\n\n"
        f"{label} preview:\n{preview}\n\n"
        f"{label} summary statistics:\n{numeric_summary}"
    )


def extract_html_text(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    return "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
