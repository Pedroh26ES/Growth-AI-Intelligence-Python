from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import requests

from growth_report.collectors.extractors import (
    extract_csv_summary,
    extract_excel_summary,
    extract_html_text,
    extract_pdf_text,
)
from growth_report.models import CollectedDocument, SourceConfig, SourceType
from growth_report.normalization import normalize_collected_document


def collect_sources(sources: list[SourceConfig], raw_dir: Path) -> list[CollectedDocument]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    documents: list[CollectedDocument] = []

    for source in sources:
        if not source.enabled:
            continue
        documents.append(_collect_source(source, raw_dir))

    return documents


def _collect_source(source: SourceConfig, raw_dir: Path) -> CollectedDocument:
    if source.type in {
        SourceType.PDF_URL,
        SourceType.CSV_URL,
        SourceType.EXCEL_URL,
        SourceType.GOOGLE_SHEETS_URL,
        SourceType.HTML_URL,
    }:
        return _collect_url(source, raw_dir)
    return _collect_file(source)


def _collect_url(source: SourceConfig, raw_dir: Path) -> CollectedDocument:
    assert source.url is not None

    request_url = _google_sheets_export_url(str(source.url)) if source.type == SourceType.GOOGLE_SHEETS_URL else str(source.url)
    response = requests.get(request_url, timeout=60)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if source.type == SourceType.HTML_URL:
        text = extract_html_text(response.text)
        return normalize_collected_document(
            CollectedDocument(
                source_name=source.name,
                source_type=source.type,
                uri=str(source.url),
                content_type=content_type or "text/html",
                text=text,
                metadata={"tags": ",".join(source.tags)},
            )
        )

    extension = _extension_for_source(source.type)
    filename = _safe_filename(source.name, request_url, extension)
    local_path = raw_dir / filename
    local_path.write_bytes(response.content)

    if extension == ".pdf":
        text = extract_pdf_text(local_path)
    elif extension in {".xlsx", ".xls"}:
        text = extract_excel_summary(local_path)
    else:
        text = extract_csv_summary(local_path)

    return normalize_collected_document(
        CollectedDocument(
            source_name=source.name,
            source_type=source.type,
            uri=str(source.url),
            content_type=content_type or _content_type_for(extension),
            text=text,
            local_path=str(local_path),
            metadata={
                "tags": ",".join(source.tags),
                "download_url": request_url,
            },
        )
    )


def _collect_file(source: SourceConfig) -> CollectedDocument:
    assert source.path is not None

    path = Path(source.path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found for '{source.name}': {path}")

    if source.type == SourceType.PDF_FILE:
        text = extract_pdf_text(path)
        content_type = "application/pdf"
    elif source.type == SourceType.CSV_FILE:
        text = extract_csv_summary(path)
        content_type = "text/csv"
    elif source.type == SourceType.EXCEL_FILE:
        text = extract_excel_summary(path)
        content_type = _content_type_for(path.suffix.lower())
    else:
        text = path.read_text(encoding="utf-8")
        content_type = "text/plain"

    return normalize_collected_document(
        CollectedDocument(
            source_name=source.name,
            source_type=source.type,
            uri=str(path),
            content_type=content_type,
            text=text,
            local_path=str(path),
            metadata={"tags": ",".join(source.tags)},
        )
    )


def _safe_filename(name: str, url: str, extension: str) -> str:
    parsed = urlparse(url)
    stem = Path(parsed.path).stem or name
    safe_stem = re.sub(r"[^a-zA-Z0-9_.-]+", "-", f"{name}-{stem}").strip("-").lower()
    return f"{safe_stem}{extension}"


def _content_type_for(extension: str) -> str:
    if extension == ".pdf":
        return "application/pdf"
    if extension in {".xlsx", ".xls"}:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "text/csv"


def _extension_for_source(source_type: SourceType) -> str:
    if source_type == SourceType.PDF_URL:
        return ".pdf"
    if source_type == SourceType.EXCEL_URL:
        return ".xlsx"
    return ".csv"


def _google_sheets_export_url(url: str) -> str:
    parsed = urlparse(url)
    if "docs.google.com" not in parsed.netloc or "/spreadsheets/d/" not in parsed.path:
        return url

    match = re.search(r"/spreadsheets/d/([^/]+)", parsed.path)
    if not match:
        return url

    sheet_id = match.group(1)
    gid_match = re.search(r"(?:[?#&]gid=)(\d+)", url)
    gid_param = f"&gid={gid_match.group(1)}" if gid_match else ""
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv{gid_param}"
