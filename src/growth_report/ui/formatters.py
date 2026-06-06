from __future__ import annotations

import re


MARKET_AVERAGE_ROAS = 4.0
BREAK_EVEN_REFERENCE_ROAS = 3.0
EXCELLENT_ROAS = MARKET_AVERAGE_ROAS * 1.25
CAMPAIGN_NAME_TRANSLATIONS = {
    "Always On Search": "Pesquisa de Marca Sempre Ativa (Always-on Brand Search)",
    "Brand Protection": "Proteção de Marca em Busca (Brand Protection Search)",
    "Content Cluster SaaS": "Cluster SEO de Comparação SaaS (SaaS Comparison SEO)",
    "Lookalike Trial": "Lookalike de Clientes de Alto Valor (High-LTV Lookalike)",
    "Newsletter Winback": "Recuperação de Clientes Inativos (Winback Email)",
    "Nurture Reactivation": "Reativação CRM de Leads Inativos (CRM Reactivation)",
    "Partner Mentions": "Indicações com Parceiros Ativos (Partner Referral)",
    "Partner Webinar": "Webinar de Co-marketing (Partner Webinar)",
    "SEO Commercial Pages": "Páginas SEO de Alta Intenção (High-Intent SEO Pages)",
    "Busca Sempre Ativa": "Pesquisa de Marca Sempre Ativa (Always-on Brand Search)",
    "Proteção de Marca": "Proteção de Marca em Busca (Brand Protection Search)",
    "Grupo de Conteúdo SaaS": "Cluster SEO de Comparação SaaS (SaaS Comparison SEO)",
    "Teste de Público Similar": "Lookalike de Clientes de Alto Valor (High-LTV Lookalike)",
    "Recuperação por E-mail": "Recuperação de Clientes Inativos (Winback Email)",
    "Reativação de Relacionamento": "Reativação CRM de Leads Inativos (CRM Reactivation)",
    "Menções de Parceiros": "Indicações com Parceiros Ativos (Partner Referral)",
    "Seminário Online de Parceiros": "Webinar de Co-marketing (Partner Webinar)",
    "Páginas Comerciais de SEO": "Páginas SEO de Alta Intenção (High-Intent SEO Pages)",
}


def money(value: float) -> str:
    return f"R$ {value:,.0f}".replace(",", ".")


def number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def change_label(value: float | None) -> str:
    if value is None:
        return "sem comparativo"
    return f"+{value:.1f}%" if value >= 0 else f"{value:.1f}%"


def trend_class(value: str) -> str:
    clean_value = value.strip()
    if clean_value.startswith("+"):
        return "trend-up"
    if clean_value.startswith("-"):
        return "trend-down"
    return "trend-neutral"


def status_class(change_pct: object) -> str:
    if not isinstance(change_pct, (int, float)):
        return "neutral"
    return "up" if change_pct >= 0 else "down"


def risk_metric(text: str) -> str:
    percent_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
    if percent_match:
        percent = percent_match.group(1).replace(",", ".")
        is_negative = any(term in text.lower() for term in ("queda", "cai", "diminu", "redu"))
        return f"-{percent}%" if is_negative else f"+{percent}%"
    return "Revisar"


def roas_tone(value: float) -> str:
    if value >= EXCELLENT_ROAS:
        return "roi-excellent"
    if value >= MARKET_AVERAGE_ROAS:
        return "roi-good"
    if value >= BREAK_EVEN_REFERENCE_ROAS:
        return "roi-watch"
    if value > 0:
        return "roi-danger"
    return "roi-neutral"


def roas_label(value: float) -> str:
    if value >= EXCELLENT_ROAS:
        return "acima da média do mercado"
    if value >= MARKET_AVERAGE_ROAS:
        return "na média do mercado"
    if value >= BREAK_EVEN_REFERENCE_ROAS:
        return "abaixo da média do mercado"
    if value > 0:
        return "crítico vs mercado"
    return "sem ROAS(Return on Ad Spend)"


def roas_market_average_label() -> str:
    return f"{MARKET_AVERAGE_ROAS:.1f}x"


def roas_break_even_label() -> str:
    return f"{BREAK_EVEN_REFERENCE_ROAS:.1f}x"


def roas_excellent_label() -> str:
    return f"{EXCELLENT_ROAS:.1f}x"


def roas_industry_benchmark_text() -> str:
    return (
        f"Padrão/média geral da indústria: {roas_market_average_label()} de "
        "ROAS(Return on Ad Spend). Ajuste por margem, setor, canal e LTV quando tiver esses dados."
    )


def campaign_display_name(name: str) -> str:
    return CAMPAIGN_NAME_TRANSLATIONS.get(name, name)


def localize_campaign_text(text: str) -> str:
    localized = text
    for original, translated in sorted(
        CAMPAIGN_NAME_TRANSLATIONS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        localized = localized.replace(original, translated)
    return localized


def campaign_investment_context(name: str, channel: str, spend: float | None = None) -> str:
    text = f"{name} {channel}"
    spend_label = "sem verba direta de mídia" if not spend else "com verba de mídia"

    if any(term in text for term in ("CRM", "Reativação", "Winback", "E-mail")):
        return (
            f"Investimento em {spend_label}: recuperar leads ou clientes que já conhecem a marca. "
            "Faz sentido porque tende a custar menos do que comprar tráfego novo."
        )
    if any(term in text for term in ("Lookalike", "Social Pago", "Paid Social")):
        return (
            f"Investimento em {spend_label}: testar públicos parecidos com clientes de maior valor. "
            "O objetivo é encontrar aquisição escalável sem perder eficiência."
        )
    if any(term in text for term in ("Marca", "Brand", "Pesquisa Paga", "Paid Search")):
        return (
            f"Investimento em {spend_label}: proteger buscas de alta intenção e capturar demanda pronta. "
            "É útil quando a marca ou termos comerciais já geram conversões."
        )
    if any(term in text for term in ("SEO", "Busca Orgânica", "Organic Search")):
        return (
            "Investimento em conteúdo, páginas e otimização orgânica. "
            "A lógica é gerar receita recorrente com menor custo direto de mídia."
        )
    if any(term in text for term in ("Parceiro", "Referral", "Indicação", "Webinar")):
        return (
            f"Investimento em {spend_label}: ativar parceiros, co-marketing ou indicações. "
            "Faz sentido para captar demanda qualificada com prova social."
        )
    return (
        f"Investimento em {spend_label}: validar se este canal consegue gerar receita, "
        "conversões e aprendizado suficiente para justificar escala."
    )
