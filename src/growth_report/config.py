from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator

from growth_report.models import SourceConfig


PLACEHOLDER_API_KEYS = {"", "coloque_sua_chave_gemini_aqui", "your-api-key", "sk-..."}
DEFAULT_PROVIDER_MODELS = {
    "gemini": "gemini-2.5-flash-lite",
    "openai": "gpt-4.1-mini",
}


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
    configured_provider = os.getenv("AI_PROVIDER", config.ai.provider).lower()
    detected_provider = detect_ai_provider(preferred_provider=configured_provider)
    if detected_provider:
        config.ai.provider = detected_provider
    elif configured_provider in ("gemini", "openai"):
        config.ai.provider = configured_provider

    if config.ai.provider == "gemini":
        model_from_env = os.getenv("GEMINI_MODEL")
    else:
        model_from_env = os.getenv("OPENAI_MODEL")

    if model_from_env:
        config.ai.model = model_from_env
    elif config.ai.provider == "openai" and config.ai.model.startswith("gemini-"):
        config.ai.model = DEFAULT_PROVIDER_MODELS["openai"]
    return config


def is_valid_api_key(value: str | None) -> bool:
    return bool(value) and value.strip() not in PLACEHOLDER_API_KEYS


def detect_ai_provider(preferred_provider: str | None = None) -> str | None:
    load_dotenv()
    providers = []
    if preferred_provider in ("gemini", "openai"):
        providers.append(preferred_provider)
    providers.extend(provider for provider in ("gemini", "openai") if provider not in providers)

    for provider in providers:
        env_name = "GEMINI_API_KEY" if provider == "gemini" else "OPENAI_API_KEY"
        if is_valid_api_key(os.getenv(env_name)):
            return provider
    return None


def is_ai_configured() -> bool:
    return detect_ai_provider() is not None


def resolve_project_path(path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path.cwd() / candidate
