from growth_report.ui.formatters import (
    campaign_display_name,
    campaign_investment_context,
    localize_campaign_text,
    roas_break_even_label,
    roas_excellent_label,
    roas_industry_benchmark_text,
    roas_label,
    roas_market_average_label,
    roas_tone,
)


def test_roas_tone_and_label_signal_investment_return() -> None:
    assert roas_tone(5.2) == "roi-excellent"
    assert roas_label(5.2) == "Acima da média do mercado"

    assert roas_tone(4.1) == "roi-good"
    assert roas_label(4.1) == "Na média do mercado"

    assert roas_tone(3.2) == "roi-watch"
    assert roas_label(3.2) == "Abaixo da média do mercado"

    assert roas_tone(2.4) == "roi-danger"
    assert roas_label(2.4) == "Crítico vs. mercado"


def test_roas_benchmark_labels_are_market_based() -> None:
    assert roas_market_average_label() == "4.0x"
    assert roas_break_even_label() == "3.0x"
    assert roas_excellent_label() == "5.0x"


def test_roas_benchmark_text_mentions_industry_standard() -> None:
    text = roas_industry_benchmark_text()

    assert "Benchmark geral de mercado" in text
    assert "4.0x" in text
    assert "Acima:" not in text
    assert "Mercado:" not in text
    assert "Abaixo:" not in text
    assert "Crítico:" not in text


def test_campaign_names_are_localized_for_dashboard_display() -> None:
    assert campaign_display_name("Brand Protection") == (
        "Proteção de Marca em Busca (Brand Protection Search)"
    )
    assert campaign_display_name("Lookalike Trial") == (
        "Lookalike de Clientes de Alto Valor (High-LTV Lookalike)"
    )
    assert campaign_display_name("Nurture Reactivation") == (
        "Reativação CRM de Leads Inativos (CRM Reactivation)"
    )

    text = "Escalar Brand Protection e revisar Lookalike Trial."

    assert localize_campaign_text(text) == (
        "Escalar Proteção de Marca em Busca (Brand Protection Search) e revisar "
        "Lookalike de Clientes de Alto Valor (High-LTV Lookalike)."
    )


def test_campaign_investment_context_explains_why_the_campaign_exists() -> None:
    crm_context = campaign_investment_context(
        "Reativação CRM de Leads Inativos (CRM Reactivation)",
        "E-mail (Email)",
        250,
    )
    lookalike_context = campaign_investment_context(
        "Lookalike de Clientes de Alto Valor (High-LTV Lookalike)",
        "Social Pago (Paid Social)",
        1800,
    )
    seo_context = campaign_investment_context(
        "Páginas SEO de Alta Intenção (High-Intent SEO Pages)",
        "Busca Orgânica (Organic Search)",
        0,
    )

    assert "recuperar leads ou clientes" in crm_context
    assert "custar menos do que comprar tráfego novo" in crm_context
    assert "públicos parecidos com clientes de maior valor" in lookalike_context
    assert "menor custo direto de mídia" in seo_context
