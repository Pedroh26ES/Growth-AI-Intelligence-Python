from pathlib import Path

from growth_report.config import detect_ai_provider, is_ai_configured, load_config


def test_detect_ai_provider_uses_any_valid_key(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    assert detect_ai_provider() == "openai"
    assert is_ai_configured() is True


def test_detect_ai_provider_ignores_placeholders(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "coloque_sua_chave_gemini_aqui")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    assert detect_ai_provider() is None
    assert is_ai_configured() is False


def test_load_config_switches_to_openai_when_only_openai_key_exists(monkeypatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    config = load_config(Path("config.example.toml"))

    assert config.ai.provider == "openai"
    assert config.ai.model == "gpt-4.1-mini"
