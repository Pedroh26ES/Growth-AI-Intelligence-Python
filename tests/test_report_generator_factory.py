from growth_report.config import AIConfig
from growth_report.services import report_generator_factory
from growth_report.services.report_generator import DryRunReportGenerator, _system_prompt


def test_factory_uses_dry_run_generator_when_requested() -> None:
    generator = report_generator_factory.build_report_generator(
        AIConfig(provider="gemini", model="gemini-test"),
        dry_run=True,
    )

    assert isinstance(generator, DryRunReportGenerator)


def test_factory_selects_configured_provider(monkeypatch) -> None:
    created = {}

    class FakeGeminiGenerator:
        def __init__(self, model: str, temperature: float) -> None:
            created["model"] = model
            created["temperature"] = temperature

    monkeypatch.setattr(report_generator_factory, "GeminiReportGenerator", FakeGeminiGenerator)

    generator = report_generator_factory.build_report_generator(
        AIConfig(provider="gemini", model="gemini-custom", temperature=0.4),
    )

    assert isinstance(generator, FakeGeminiGenerator)
    assert created == {"model": "gemini-custom", "temperature": 0.4}


def test_report_prompt_requires_brazilian_portuguese() -> None:
    prompt = _system_prompt()

    assert "português do Brasil" in prompt
    assert "Todo texto narrativo do JSON" in prompt
