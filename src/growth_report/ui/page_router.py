from __future__ import annotations

from growth_report.models import ReportCollection, WeeklyGrowthReport
from growth_report.ui.pages import actions, campaigns, channels, data, history, imports, overview


NAV_LABELS = ["HOME", "HISTORICO", "CANAIS", "CAMPANHAS", "ACOES", "DADOS", "IMPORTAR"]

PAGE_BY_LABEL = {
    "HOME": "Visão geral",
    "HISTORICO": "Histórico",
    "CANAIS": "Canais",
    "CAMPANHAS": "Campanhas",
    "ACOES": "Ações",
    "DADOS": "Dados",
    "IMPORTAR": "Importar",
}

PAGE_DESCRIPTIONS = {
    "Visão geral": "Resumo executivo da semana, com os números principais e as decisões que merecem atenção.",
    "Histórico": "Acompanhe a evolução dos relatórios semanais e compare o desempenho entre períodos.",
    "Canais": "Entenda quais canais puxaram crescimento, quais caíram e onde investigar primeiro.",
    "Campanhas": "Filtre campanhas por canal, receita, ROAS(Return on Ad Spend) e conversões para decidir onde investir.",
    "Ações": "Quadro de decisões por prioridade para orientar o trabalho da próxima semana.",
    "Dados": "Dados do relatório organizados para leitura e auditoria, sem depender de tabelas cruas.",
    "Importar": "Importe PDFs, CSVs, planilhas Excel e links do Google Sheets para gerar o relatório.",
}


def page_from_label(label: str) -> str:
    return PAGE_BY_LABEL[label]


def page_description(page: str, fallback: str) -> str:
    return PAGE_DESCRIPTIONS.get(page, fallback)


def render_page(
    page: str,
    report: WeeklyGrowthReport,
    collection: ReportCollection,
    ui,
) -> None:
    if page == "Visão geral":
        overview.render(report, collection, ui)
    elif page == "Histórico":
        history.render(collection, report, ui)
    elif page == "Canais":
        channels.render(report, collection, ui)
    elif page == "Campanhas":
        campaigns.render(report, ui)
    elif page == "Ações":
        actions.render(report, ui)
    elif page == "Importar":
        imports.render(ui)
    else:
        data.render(report, ui)
