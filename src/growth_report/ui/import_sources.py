from __future__ import annotations

import json
import re
from pathlib import Path

from growth_report.models import SourceConfig, SourceType


DEFAULT_IMPORTS_DIR = Path("data/raw/imports")
IMPORTED_SOURCES_PATH = Path("data/imported_sources.json")


def load_imported_sources() -> list[SourceConfig]:
    if not IMPORTED_SOURCES_PATH.exists():
        return []
    payload = json.loads(IMPORTED_SOURCES_PATH.read_text(encoding="utf-8"))
    return [SourceConfig.model_validate(source) for source in payload.get("sources", [])]


def save_imported_sources(sources: list[SourceConfig]) -> None:
    IMPORTED_SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"sources": [source.model_dump(mode="json") for source in sources]}
    IMPORTED_SOURCES_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def save_uploaded_source(uploaded_file) -> SourceConfig:
    DEFAULT_IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = safe_import_filename(uploaded_file.name)
    path = DEFAULT_IMPORTS_DIR / filename
    path.write_bytes(uploaded_file.getbuffer())

    return SourceConfig(
        name=Path(filename).stem.replace("-", " ").title(),
        type=source_type_for_filename(filename),
        path=str(path),
        enabled=True,
        tags=["uploaded", Path(filename).suffix.lower().lstrip(".")],
    )


def safe_import_filename(filename: str) -> str:
    path = Path(filename)
    stem = re.sub(r"[^a-zA-Z0-9_.-]+", "-", path.stem).strip("-").lower() or "source"
    suffix = path.suffix.lower()
    return f"{stem}{suffix}"


def source_type_for_filename(filename: str) -> SourceType:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return SourceType.PDF_FILE
    if suffix == ".csv":
        return SourceType.CSV_FILE
    if suffix in {".xlsx", ".xls"}:
        return SourceType.EXCEL_FILE
    raise ValueError(f"Formato nao suportado: {suffix}")


def merge_sources(existing: list[SourceConfig], new_sources: list[SourceConfig]) -> list[SourceConfig]:
    merged: dict[str, SourceConfig] = {}
    for source in [*existing, *new_sources]:
        key = str(source.url or source.path or source.name)
        merged[key] = source
    return list(merged.values())
