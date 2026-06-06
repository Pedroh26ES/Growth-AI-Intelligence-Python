from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Iterable

import pandas as pd

from growth_report.models import CollectedDocument, NormalizedGrowthRecord, SourceType

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "campaign": (
        "campaign",
        "campaign name",
        "campanha",
        "nome da campanha",
        "nome campanha",
        "ad campaign",
    ),
    "channel": (
        "channel",
        "canal",
        "source",
        "origem",
        "media",
        "midia",
        "platform",
        "plataforma",
    ),
    "spend": (
        "cost",
        "spend",
        "investment",
        "investimento",
        "custo",
        "valor investido",
        "amount spent",
    ),
    "clicks": ("clicks", "cliques", "link clicks", "click"),
    "conversions": (
        "conversions",
        "conversoes",
        "conversao",
        "leads",
        "lead",
        "vendas",
        "sales",
        "purchases",
        "resultados",
    ),
    "revenue": (
        "revenue",
        "receita",
        "faturamento",
        "valor receita",
        "valor de receita",
        "receita gerada",
    ),
}

NUMERIC_FIELDS = {"spend", "clicks", "conversions", "revenue"}
STRUCTURED_SOURCE_TYPES = {
    SourceType.CSV_FILE,
    SourceType.CSV_URL,
    SourceType.GOOGLE_SHEETS_URL,
    SourceType.EXCEL_FILE,
    SourceType.EXCEL_URL,
}


def normalize_collected_document(document: CollectedDocument) -> CollectedDocument:
    records: list[NormalizedGrowthRecord] = []
    notes: list[str] = []

    if document.source_type in STRUCTURED_SOURCE_TYPES and document.local_path:
        records, notes = _normalize_structured_file(document)
    elif document.source_type in {SourceType.PDF_FILE, SourceType.PDF_URL, SourceType.TEXT_FILE}:
        records, notes = _normalize_unstructured_text(document)
    else:
        notes = ["Fonte mantida como texto livre; nenhum schema tabular foi detectado."]

    return document.model_copy(
        update={
            "normalized_records": records,
            "normalization_notes": notes,
        }
    )


def _normalize_structured_file(
    document: CollectedDocument,
) -> tuple[list[NormalizedGrowthRecord], list[str]]:
    path = Path(document.local_path or "")

    if document.source_type in {SourceType.EXCEL_FILE, SourceType.EXCEL_URL}:
        workbook = pd.ExcelFile(path)
        records: list[NormalizedGrowthRecord] = []
        notes: list[str] = []
        for sheet_name in workbook.sheet_names:
            dataframe = workbook.parse(sheet_name)
            source_kind = identify_source_kind(
                document.source_name,
                document.metadata.get("tags", ""),
                dataframe.columns,
            )
            sheet_records, sheet_notes = normalize_dataframe(
                dataframe,
                source_name=document.source_name,
                source_kind=source_kind,
                sheet_name=sheet_name,
            )
            records.extend(sheet_records)
            notes.extend(sheet_notes)
        return records, _dedupe(notes)

    dataframe = pd.read_csv(path)
    source_kind = identify_source_kind(
        document.source_name,
        document.metadata.get("tags", ""),
        dataframe.columns,
    )
    return normalize_dataframe(
        dataframe,
        source_name=document.source_name,
        source_kind=source_kind,
    )


def normalize_dataframe(
    dataframe: pd.DataFrame,
    *,
    source_name: str,
    source_kind: str,
    sheet_name: str | None = None,
) -> tuple[list[NormalizedGrowthRecord], list[str]]:
    column_map = map_equivalent_columns(dataframe.columns)
    notes: list[str] = []
    missing = sorted({"campaign", "spend", "conversions", "revenue"} - set(column_map))
    if missing:
        notes.append(f"Campos ausentes ou nao mapeados: {', '.join(missing)}.")

    records: list[NormalizedGrowthRecord] = []
    for index, row in dataframe.iterrows():
        record = _record_from_row(
            row,
            column_map,
            source_name=source_name,
            source_kind=source_kind,
            sheet_name=sheet_name,
            row_number=int(index) + 2,
        )
        if record is not None:
            records.append(record)

    if not records:
        notes.append("Nenhum registro de growth foi normalizado desta fonte.")
    else:
        notes.append(f"{len(records)} registro(s) normalizado(s) para o schema interno.")

    return records, notes


def map_equivalent_columns(columns: Iterable[str]) -> dict[str, str]:
    normalized_columns = {_normalize_label(str(column)): str(column) for column in columns}
    mapped: dict[str, str] = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            normalized_alias = _normalize_label(alias)
            if normalized_alias in normalized_columns:
                mapped[field] = normalized_columns[normalized_alias]
                break
    return mapped


def identify_source_kind(source_name: str, tags: str = "", columns: Iterable[str] = ()) -> str:
    source_haystack = _normalize_label(" ".join([source_name, tags]))
    full_haystack = _normalize_label(" ".join([source_name, tags, " ".join(map(str, columns))]))
    if any(term in source_haystack for term in ("google ads", "adwords", "pesquisa paga")):
        return "google_ads"
    if any(term in source_haystack for term in ("meta ads", "facebook ads", "instagram ads", "social pago")):
        return "meta_ads"
    if any(term in source_haystack for term in ("crm", "hubspot", "salesforce")):
        return "crm"
    if any(term in source_haystack for term in ("sheets", "google sheets", "planilha")):
        return "google_sheets"
    if "pdf" in full_haystack:
        return "pdf_report"
    return "manual_export"


def _record_from_row(
    row: pd.Series,
    column_map: dict[str, str],
    *,
    source_name: str,
    source_kind: str,
    sheet_name: str | None,
    row_number: int,
) -> NormalizedGrowthRecord | None:
    values = {field: row.get(column) for field, column in column_map.items()}
    numeric_values = {field: _parse_number(values.get(field)) for field in NUMERIC_FIELDS}
    if all(value is None for value in numeric_values.values()):
        return None

    campaign = _as_text(values.get("campaign")) or source_name
    channel = _as_text(values.get("channel")) or _channel_from_source_kind(source_kind)

    return NormalizedGrowthRecord(
        source_name=source_name,
        source_kind=source_kind,
        row_number=row_number,
        sheet_name=sheet_name,
        channel=channel,
        campaign=campaign,
        spend=numeric_values["spend"],
        clicks=numeric_values["clicks"],
        conversions=numeric_values["conversions"],
        revenue=numeric_values["revenue"],
        raw_values={column: _as_text(row.get(column)) for column in row.index},
    )


def _normalize_unstructured_text(
    document: CollectedDocument,
) -> tuple[list[NormalizedGrowthRecord], list[str]]:
    source_kind = identify_source_kind(
        document.source_name,
        document.metadata.get("tags", ""),
        ["pdf"] if document.source_type in {SourceType.PDF_FILE, SourceType.PDF_URL} else [],
    )
    records: list[NormalizedGrowthRecord] = []
    for index, match in enumerate(_campaign_metric_matches(document.text), start=1):
        records.append(
            NormalizedGrowthRecord(
                source_name=document.source_name,
                source_kind=source_kind,
                row_number=index,
                channel=_channel_from_source_kind(source_kind),
                campaign=match["campaign"],
                conversions=_parse_number(match.get("conversions")),
                revenue=_parse_number(match.get("revenue")),
                raw_values={key: value for key, value in match.items() if value},
            )
        )

    if records:
        return records, [f"{len(records)} registro(s) extraido(s) de texto livre por padrao textual."]
    return [], ["Texto livre coletado; nenhum padrao de campanha/metrica foi encontrado."]


def _campaign_metric_matches(text: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r"(?:campanha|campaign)\s+(?P<campaign>[^.\n]{2,80}?)\s+"
        r"(?:teve|gerou|registrou|had|generated)\s+"
        r"(?P<conversions>[\d.,]+)\s+"
        r"(?:leads|convers(?:o|õ)es|vendas|sales|purchases)"
        r".{0,120}?"
        r"(?:R\$\s*)?(?P<revenue>[\d.,]+)\s+"
        r"(?:de\s+)?(?:receita|revenue|faturamento)",
        flags=re.IGNORECASE,
    )
    return [match.groupdict() for match in pattern.finditer(text)]


def _parse_number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, int | float):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    text = re.sub(r"[^\d,.\-]", "", text)
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+", text):
        text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return None


def _as_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", without_accents.lower()).strip()


def _channel_from_source_kind(source_kind: str) -> str:
    return {
        "google_ads": "Pesquisa Paga (Paid Search)",
        "meta_ads": "Social Pago (Paid Social)",
        "crm": "CRM",
        "google_sheets": "Planilha (Google Sheets)",
        "pdf_report": "Relatorio PDF",
    }.get(source_kind, "Fonte Manual")


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
