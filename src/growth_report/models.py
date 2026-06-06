from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SourceType(StrEnum):
    PDF_URL = "pdf_url"
    PDF_FILE = "pdf_file"
    CSV_URL = "csv_url"
    CSV_FILE = "csv_file"
    EXCEL_URL = "excel_url"
    EXCEL_FILE = "excel_file"
    GOOGLE_SHEETS_URL = "google_sheets_url"
    HTML_URL = "html_url"
    TEXT_FILE = "text_file"


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: SourceType
    url: HttpUrl | None = None
    path: str | None = None
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)


class NormalizedGrowthRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str
    source_kind: str
    row_number: int | None = None
    sheet_name: str | None = None
    channel: str
    campaign: str
    spend: float | None = None
    clicks: float | None = None
    conversions: float | None = None
    revenue: float | None = None
    currency: str = "BRL"
    raw_values: dict[str, str] = Field(default_factory=dict)


class CollectedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str
    source_type: SourceType
    uri: str
    content_type: str
    text: str
    local_path: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    normalized_records: list[NormalizedGrowthRecord] = Field(default_factory=list)
    normalization_notes: list[str] = Field(default_factory=list)


class RateMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: float
    unit: str = "%"
    change_pct: float | None = None
    context: str = ""


class ChannelStatus(StrEnum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    WATCH = "watch"


class ChannelInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: str
    status: ChannelStatus
    current_value: float | None = None
    previous_value: float | None = None
    change_pct: float | None = None
    summary: str


class CampaignInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    channel: str
    objective: str = ""
    spend: float | None = None
    conversions: float | None = None
    revenue: float | None = None
    roas: float | None = None
    summary: str


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    priority: Priority
    action: str
    rationale: str
    owner_suggestion: str = ""
    expected_impact: str = ""


class WeeklyGrowthReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    week_start: date
    week_end: date
    generated_at: datetime
    executive_summary: str
    intro: str
    performance: str
    risks: list[str]
    rates: list[RateMetric]
    opportunities: list[str]
    recommendations: list[Recommendation]
    channels: list[ChannelInsight]
    campaigns: list[CampaignInsight]
    conclusion: str
    sources: list[str]
    confidence_notes: list[str] = Field(
        default_factory=list,
        description="Notes about incomplete, low-confidence, or missing data.",
    )


class ReportCollection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reports: list[WeeklyGrowthReport] = Field(default_factory=list)
