from __future__ import annotations

from growth_report.config import AIConfig
from growth_report.services.report_generator import (
    DryRunReportGenerator,
    GeminiReportGenerator,
    OpenAIReportGenerator,
    ReportGenerator,
)


def build_report_generator(ai_config: AIConfig, *, dry_run: bool = False) -> ReportGenerator:
    if dry_run:
        return DryRunReportGenerator()

    if ai_config.provider == "gemini":
        return GeminiReportGenerator(
            model=ai_config.model,
            temperature=ai_config.temperature,
        )

    return OpenAIReportGenerator(
        model=ai_config.model,
        temperature=ai_config.temperature,
    )
