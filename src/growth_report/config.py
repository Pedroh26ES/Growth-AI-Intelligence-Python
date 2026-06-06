from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator

from growth_report.models import SourceConfig


class AIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["gemini", "openai"] = "gemini"
    model: str = "gemini-3.5-flash"
    temperature: float = 0.2


class StorageConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reports_path: Path = Path("data/reports/weekly_reports.json")
    raw_dir: Path = Path("data/raw")


class SchedulerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timezone: str = "America/Sao_Paulo"
    day_of_week: str = "mon"
    hour: int = 6
    minute: int = 0


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ai: AIConfig = Field(default_factory=AIConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    sources: list[SourceConfig] = Field(default_factory=list)

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, sources: list[SourceConfig]) -> list[SourceConfig]:
        for source in sources:
            if source.type.value.endswith("_url") and source.url is None:
                raise ValueError(f"Source '{source.name}' requires url.")
            if source.type.value.endswith("_file") and source.path is None:
                raise ValueError(f"Source '{source.name}' requires path.")
        return sources


def load_config(config_path: Path | None = None) -> AppConfig:
    load_dotenv()

    configured_path = config_path or Path(
        os.getenv("GROWTH_CONFIG_PATH", "config.example.toml")
    )
    if not configured_path.exists():
        raise FileNotFoundError(f"Config file not found: {configured_path}")

    with configured_path.open("rb") as file:
        raw_config = tomllib.load(file)

    config = AppConfig.model_validate(raw_config)
    provider_from_env = os.getenv("AI_PROVIDER")
    if provider_from_env:
        config.ai.provider = provider_from_env.lower()

    if config.ai.provider == "gemini":
        model_from_env = os.getenv("GEMINI_MODEL")
    else:
        model_from_env = os.getenv("OPENAI_MODEL")

    if model_from_env:
        config.ai.model = model_from_env
    return config


def resolve_project_path(path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path.cwd() / candidate
