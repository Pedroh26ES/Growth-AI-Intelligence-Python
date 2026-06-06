from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from growth_report.models import ReportCollection, SourceConfig, WeeklyGrowthReport
from growth_report.ui.formatters import (
    campaign_display_name as _campaign_display_name,
    campaign_investment_context as _campaign_investment_context,
    change_label as _change_label,
    localize_campaign_text as _localize_campaign_text,
    money as _money,
    number as _number,
    roas_industry_benchmark_text as _roas_industry_benchmark_text,
    roas_label as _roas_label,
    roas_market_average_label as _roas_market_average_label,
    roas_tone as _roas_tone,
    risk_metric as _risk_metric,
    status_class as _status_class,
    trend_class as _trend_class,
)
from growth_report.ui.import_sources import (
    load_imported_sources as _load_imported_sources,
    merge_sources as _merge_sources,
    save_imported_sources as _save_imported_sources,
    save_uploaded_source as _save_uploaded_source,
)
from growth_report.ui.metrics import (
    channel_comparisons as _channel_comparisons,
    percent_delta as _percent_delta,
    previous_report as _previous_report,
    priority_count as _priority_count,
    rate_label as _rate_label,
    report_conversions as _report_conversions,
    report_revenue as _report_revenue,
    report_roas as _report_roas,
    safe_div as _safe_div,
)


def _history_summary(reports: list[WeeklyGrowthReport]) -> None:
    total_revenue = sum(_report_revenue(report) for report in reports)
    total_conversions = sum(_report_conversions(report) for report in reports)
    average_roas = _safe_div(
        sum(_report_revenue(report) for report in reports),
        sum(sum((campaign.spend or 0) for campaign in report.campaigns) for report in reports),
    )
    cols = st.columns(4)
    _mini_card(cols[0], "Relatórios", str(len(reports)), "semanas no histórico")
    _mini_card(cols[1], "Receita total", _money(total_revenue), "todos os relatórios")
    _mini_card(cols[2], "Conversões", _number(total_conversions), "todos os relatórios")
    _mini_card(
        cols[3],
        "ROAS(Return on Ad Spend) médio",
        f"{average_roas:.2f}x" if average_roas else "-",
        "histórico",
    )


def _history_timeline(reports: list[WeeklyGrowthReport], selected_report: WeeklyGrowthReport) -> None:
    max_revenue = max((_report_revenue(report) for report in reports), default=0)
    if max_revenue <= 0:
        st.info("Sem histórico de receita para exibir.")
        return

    rows = []
    previous_revenue = None
    for report in reports:
        revenue = _report_revenue(report)
        roas = _report_roas(report)
        width = max(5, round((revenue / max_revenue) * 100))
        tone = _roas_tone(roas)
        delta = _percent_delta(revenue, previous_revenue) if previous_revenue else None
        delta_label = _change_label(delta) if delta is not None else "base inicial"
        delta_class = _trend_class(delta_label)
        roas_value = f"{roas:.2f}x ROAS(Return on Ad Spend)" if roas else "sem ROAS(Return on Ad Spend)"
        selected = "selected" if report.report_id == selected_report.report_id else ""
        rows.append(
            f'<div class="timeline-row {selected} {tone}">'
            f'<strong>{report.week_start:%d/%m}</strong>'
            f'<div class="timeline-main">'
            f'<div class="bar-track"><div class="bar-fill {tone}" style="width:{width}%"></div></div>'
            f'<small class="{delta_class}">{escape(delta_label)}</small>'
            f"</div>"
            f'<div class="timeline-value">'
            f'<span>{_money(revenue)}</span>'
            f'<b class="roas-pill {tone}">{escape(roas_value)}</b>'
            f"</div>"
            f"</div>"
        )
        previous_revenue = revenue

    st.markdown(
        '<div class="timeline-help">'
        '<strong>Como ler as cores:</strong> o benchmark geral usado é '
        f'{escape(_roas_market_average_label())} de ROAS(Return on Ad Spend). '
        'Isso significa que cada R$ 1 investido em mídia gera cerca de R$ 4 em receita. '
        'A regra pode ser ajustada por setor ou canal quando você tiver esse dado.'
        "</div>"
        f'<div class="chart-card timeline-card">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )


def _channel_action(change: object) -> str:
    if not isinstance(change, (int, float)):
        return "Aguardar mais um relatório para comparar com segurança."
    if change <= -20:
        return "Corrigir este canal antes de escalar verba."
    if change < 0:
        return "Revisar a causa da queda e acompanhar recuperação."
    if change >= 20:
        return "Escalar com controle de orçamento e frequência."
    return "Manter operação e testar ganho incremental."


def _channel_diagnostic_grid(channels: list[dict[str, object]]) -> None:
    rows = []
    for channel in sorted(channels, key=lambda item: float(item["current"]), reverse=True):
        current = float(channel["current"])
        previous = channel["previous"]
        change = channel["change_pct"]
        share = float(channel["share"])
        status_class = _status_class(change)
        previous_label = _money(float(previous)) if previous is not None else "-"
        previous_week = str(channel.get("previous_week") or "sem histórico anterior")
        change_label = _change_label(change if isinstance(change, (int, float)) else None)
        action = _channel_action(change)
        rows.append(
            f'<div class="channel-diagnostic {status_class}">'
            f'<div class="diagnostic-head">'
            f'<div><span>{escape(str(channel["status"]))}</span><strong>{escape(str(channel["channel"]))}</strong></div>'
            f'<b class="badge {status_class}">{escape(change_label)}</b>'
            f"</div>"
            f'<div class="channel-compare">'
            f'<div><span>Atual</span><strong>{_money(current)}</strong></div>'
            f'<div><span>Semana anterior</span><strong>{previous_label}</strong><small>{escape(previous_week)}</small></div>'
            f"</div>"
            f'<div class="channel-share">'
            f'<div class="channel-share-top"><span>Peso na receita</span><strong>{share:.1f}%</strong></div>'
            f'<div class="share-track"><div class="share-fill {status_class}" style="width:{max(3, round(share))}%"></div></div>'
            f'<small>Percentual da receita total da semana selecionada.</small>'
            f"</div>"
            f'<div class="channel-action {status_class}"><span>Ação recomendada</span><strong>{escape(action)}</strong></div>'
            f"</div>"
        )
    st.markdown(f'<div class="channel-diagnostic-grid">{"".join(rows)}</div>', unsafe_allow_html=True)


def _channel_priority_action(channels: list[dict[str, object]]) -> None:
    comparable = [
        channel
        for channel in channels
        if isinstance(channel.get("change_pct"), (int, float))
    ]
    if not comparable:
        st.info("Ainda não existe relatório anterior para definir uma prioridade por canal.")
        return

    falling = [channel for channel in comparable if float(channel["change_pct"]) < 0]
    if falling:
        target = min(falling, key=lambda item: float(item["change_pct"]))
        tone = "down"
        title = f"Revisar {target['channel']} primeiro"
        basis = "maior queda contra a semana anterior"
    else:
        target = max(comparable, key=lambda item: float(item["change_pct"]))
        tone = "up"
        title = f"Escalar {target['channel']} com controle"
        basis = "maior crescimento contra a semana anterior"

    change = target["change_pct"]
    st.markdown(
        f'<div class="channel-priority-card {tone}">'
        f'<span>Prioridade única da página</span>'
        f'<strong>{escape(title)}</strong>'
        f'<p>{escape(_change_label(change if isinstance(change, (int, float)) else None))} '
        f'foi o sinal mais importante: {escape(basis)}. '
        f'{escape(_channel_action(change))}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _source_audit(report: WeeklyGrowthReport) -> None:
    st.markdown('<div class="section-label">Fontes processadas</div>', unsafe_allow_html=True)
    if not report.sources:
        st.info("Nenhuma fonte registrada.")
        return

    cards = []
    for index, source in enumerate(report.sources, start=1):
        label = Path(source).name if not source.startswith("http") else source.split("/")[2]
        cards.append(
            f'<div class="audit-card">'
            f'<span>Fonte {index}</span>'
            f'<strong>{escape(label)}</strong>'
            f'<small>{escape(source)}</small>'
            f"</div>"
        )
    st.markdown(f'<div class="audit-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def _rates_audit(report: WeeklyGrowthReport) -> None:
    st.markdown('<div class="section-label">Métricas extraídas</div>', unsafe_allow_html=True)
    if not report.rates:
        st.info("Nenhuma taxa extraída.")
        return

    for rate in report.rates:
        value = f"{rate.value:.1f}{rate.unit}" if rate.unit != "x" else f"{rate.value:.2f}x"
        tone = "trend-up" if rate.value >= 0 else "trend-down"
        st.markdown(
            f'<div class="audit-metric">'
            f'<div><span>{escape(rate.name)}</span><small>{escape(rate.context)}</small></div>'
            f'<strong class="{tone}">{escape(value)}</strong>'
            f"</div>",
            unsafe_allow_html=True,
        )


def _confidence_audit(report: WeeklyGrowthReport) -> None:
    if not report.confidence_notes:
        return

    st.markdown('<div class="section-label spacing-top">Observações de confiança</div>', unsafe_allow_html=True)
    for note in report.confidence_notes:
        st.markdown(f'<div class="audit-note">{escape(note)}</div>', unsafe_allow_html=True)


def _kpi_row(report: WeeklyGrowthReport) -> None:
    revenue = _report_revenue(report)
    conversions = _report_conversions(report)
    roas = _report_roas(report)

    cols = st.columns(4)
    _metric_card(
        cols[0],
        "Receita",
        _money(revenue),
        _rate_label(report, "Revenue Growth"),
        "green",
        "R$",
        "Soma da receita atribuída às campanhas da semana. Use para medir o tamanho do resultado gerado.",
    )
    _metric_card(
        cols[1],
        "Conversões",
        _number(conversions),
        _rate_label(report, "Conversions Growth"),
        "amber",
        "OK",
        "Total de ações convertidas na semana, como leads, trials, vendas ou outro objetivo configurado.",
    )
    _metric_card(
        cols[2],
        "ROAS(Return on Ad Spend) médio",
        f"{roas:.2f}x" if roas else "-",
        _roas_label(roas) if roas else "sem benchmark",
        "blue",
        "RX",
        (
            "ROAS(Return on Ad Spend): receita gerada para cada R$ 1 investido em mídia.\n\n"
            f"{_roas_industry_benchmark_text()}"
        ),
    )
    _metric_card(
        cols[3],
        "Riscos",
        str(len(report.risks)),
        _priority_count(report),
        "coral",
        "AT",
        "Quantidade de pontos que podem prejudicar o desempenho da próxima semana e precisam de acompanhamento.",
    )


def _comparison_strip(report: WeeklyGrowthReport, collection: ReportCollection) -> None:
    previous = _previous_report(report, collection)
    if previous is None:
        return

    revenue_delta = _percent_delta(_report_revenue(report), _report_revenue(previous))
    conversion_delta = _percent_delta(_report_conversions(report), _report_conversions(previous))
    risk_delta = len(report.risks) - len(previous.risks)
    previous_revenue_rate = _rate_label(previous, "Revenue Growth")
    previous_conversion_rate = _rate_label(previous, "Conversions Growth")

    cols = st.columns(3)
    _mini_card(cols[0], "Receita vs semana anterior", _change_label(revenue_delta), f"semana anterior: {previous_revenue_rate}")
    _mini_card(cols[1], "Conversões vs semana anterior", _change_label(conversion_delta), f"semana anterior: {previous_conversion_rate}")
    _mini_card(cols[2], "Riscos vs semana anterior", f"{risk_delta:+d}", f"antes: {len(previous.risks)} risco(s)")


def _executive_focus(report: WeeklyGrowthReport, collection: ReportCollection) -> None:
    st.markdown('<div class="section-label">Foco executivo</div>', unsafe_allow_html=True)
    channel_rows = _channel_comparisons(report, collection)
    comparable_channels = [
        channel for channel in channel_rows
        if isinstance(channel["change_pct"], (int, float))
    ]
    positive_channels = [
        channel for channel in comparable_channels
        if float(channel["change_pct"]) >= 0
    ]
    negative_channels = [
        channel for channel in comparable_channels
        if float(channel["change_pct"]) < 0
    ]
    best_channel = max(positive_channels, key=lambda channel: float(channel["change_pct"]), default=None)
    worst_channel = min(negative_channels, key=lambda channel: float(channel["change_pct"]), default=None)
    best_campaign = max(
        report.campaigns,
        key=lambda campaign: (campaign.roas or 0, campaign.revenue or 0),
        default=None,
    )
    best_campaign_tone = _roas_tone(best_campaign.roas or 0) if best_campaign else "roi-neutral"
    best_campaign_is_market_level = best_campaign_tone in {"roi-excellent", "roi-good"}

    items = [
        {
            "action": "Escalar investimento",
            "title": _campaign_display_name(best_campaign.name) if best_campaign else "Sem campanha",
            "metric": f"{best_campaign.roas:.2f}x ROAS" if best_campaign and best_campaign.roas else "ver detalhe",
            "body": (
                f"Melhor campanha para receber mais verba nesta semana. Canal: {best_campaign.channel}. "
                f"Benchmark: {_roas_label(best_campaign.roas or 0)}."
            )
            if best_campaign else "Ainda não há campanha suficiente para escalar.",
            "tone": "success" if best_campaign_is_market_level else "neutral",
            "metric_class": "trend-up" if best_campaign_is_market_level else "trend-neutral",
        },
        {
            "action": "Investigar queda",
            "title": str(worst_channel["channel"]) if worst_channel else "Sem alerta",
            "metric": _change_label(float(worst_channel["change_pct"]) if worst_channel else None),
            "body": _localize_campaign_text(str(worst_channel["summary"])) if worst_channel else "Nenhum canal em queda relevante.",
            "tone": "danger" if worst_channel else "neutral",
            "metric_class": _trend_class(_change_label(float(worst_channel["change_pct"]) if worst_channel else None)),
        },
        {
            "action": "Manter forte",
            "title": str(best_channel["channel"]) if best_channel else "Sem destaque",
            "metric": _change_label(float(best_channel["change_pct"]) if best_channel else None),
            "body": _localize_campaign_text(str(best_channel["summary"])) if best_channel else "Sem canal com crescimento comprovado nesse período.",
            "tone": "success" if best_channel else "neutral",
            "metric_class": _trend_class(_change_label(float(best_channel["change_pct"]) if best_channel else None)),
        },
    ]
    cards = []
    for item in items:
        cards.append(
            f'<div class="focus-card {item["tone"]}">'
            f'<div class="focus-top">'
            f'<span>{escape(item["action"])}</span>'
            f'<b class="{item["metric_class"]}">{escape(item["metric"])}</b>'
            f"</div>"
            f'<strong>{escape(item["title"])}</strong>'
            f'<p>{escape(item["body"])}</p>'
            f"</div>"
        )
    st.markdown(f'<div class="focus-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def _metric_card(column, label: str, value: str, note: str, tone: str, icon: str, help_text: str) -> None:
    note_tone = _trend_class(note)
    column.markdown(
        f"""
        <div class="metric-card {tone}">
          <div class="metric-head">
            <span>{escape(label)}</span>
            <span class="info-popover" tabindex="0" aria-label="Explicar {escape(label)}">
              <span class="info-trigger">!</span>
              <span class="info-panel">{escape(help_text)}</span>
            </span>
          </div>
          <div class="metric-body">
            <div>
              <strong>{escape(value)}</strong>
              <small class="{note_tone}">{escape(note)}</small>
            </div>
            <div class="metric-icon">{escape(icon)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _next_steps_panel(report: WeeklyGrowthReport, limit: int | None = None) -> None:
    st.markdown('<div class="section-label">O que fazer agora</div>', unsafe_allow_html=True)
    if not report.recommendations:
        st.warning("Sem recomendações.")
        return

    priority_order = {"high": 0, "medium": 1, "low": 2}
    cards = []
    for index, item in enumerate(
        sorted(report.recommendations, key=lambda row: priority_order.get(row.priority.value, 9))[:limit],
        start=1,
    ):
        cards.append(
            f'<div class="step-card">'
            f'<span>{index}</span>'
            f'<div>'
            f'<strong>{escape(_localize_campaign_text(item.action))}</strong>'
            f'<p>{escape(_localize_campaign_text(item.expected_impact or item.rationale))}</p>'
            f'</div>'
            f'</div>'
        )
    st.markdown(f'<div class="next-steps-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def _campaign_summary(campaigns) -> None:
    total_revenue = sum((campaign.revenue or 0) for campaign in campaigns)
    total_spend = sum((campaign.spend or 0) for campaign in campaigns)
    paid_roas = total_revenue / total_spend if total_spend else None
    best = max(campaigns, key=lambda campaign: (campaign.roas or 0, campaign.revenue or 0))

    cols = st.columns(3)
    _mini_card(cols[0], "Receita filtrada", _money(total_revenue), "soma das campanhas")
    _mini_card(
        cols[1],
        "ROAS(Return on Ad Spend) filtrado",
        f"{paid_roas:.2f}x" if paid_roas else "-",
        _roas_label(paid_roas) if paid_roas else "sem benchmark",
    )
    _mini_card(cols[2], "Destaque", _campaign_display_name(best.name), f"{best.channel}")


def _roas_benchmark_note() -> None:
    return


def _mini_card(column, label: str, value: str, note: str) -> None:
    value_tone = _trend_class(value)
    column.markdown(
        f"""
        <div class="mini-card">
          <span>{escape(label)}</span>
          <strong class="{value_tone}">{escape(value)}</strong>
          <small>{escape(note)}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _action_board(report: WeeklyGrowthReport) -> None:
    st.markdown('<div class="section-label">Quadro de decisão</div>', unsafe_allow_html=True)
    groups = [
        ("high", "Alta prioridade", "Fazer primeiro"),
        ("medium", "Média prioridade", "Planejar"),
        ("low", "Baixa prioridade", "Monitorar"),
    ]
    cols = st.columns(3)
    for column, (priority, title, subtitle) in zip(cols, groups, strict=False):
        items = [item for item in report.recommendations if item.priority.value == priority]
        cards = []
        for item in items:
            cards.append(
                f'<div class="board-card">'
                f'<strong>{escape(_localize_campaign_text(item.action))}</strong>'
                f'<p>{escape(_localize_campaign_text(item.rationale))}</p>'
                f'<small>{escape(_localize_campaign_text(item.expected_impact))}</small>'
                f"</div>"
            )
        if not cards:
            cards.append('<div class="board-empty">Nada aqui por enquanto.</div>')
        column.markdown(
            f'<div class="board-column {priority}">'
            f'<span>{escape(subtitle)}</span>'
            f'<h3>{escape(title)}</h3>'
            f'{"".join(cards)}'
            f"</div>",
            unsafe_allow_html=True,
        )


def _risk_list(report: WeeklyGrowthReport, limit: int | None = None) -> None:
    st.markdown('<div class="section-label spacing-top">Pontos de atenção</div>', unsafe_allow_html=True)
    if not report.risks:
        st.success("Nenhum risco relevante identificado.")
        return

    cards = []
    for index, risk in enumerate(report.risks[:limit], start=1):
        metric = _risk_metric(risk)
        cards.append(
            f'<div class="risk-card">'
            f'<div class="risk-head">'
            f'<span>Alerta {index}</span>'
            f'<b class="{_trend_class(metric)}">{escape(metric)}</b>'
            f"</div>"
            f"<p>{escape(_localize_campaign_text(risk))}</p>"
            f"</div>"
        )
    st.markdown(f'<div class="risk-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def _opportunities(report: WeeklyGrowthReport) -> None:
    if not report.opportunities:
        return

    st.markdown('<div class="section-label spacing-top">Oportunidades</div>', unsafe_allow_html=True)
    for opportunity in report.opportunities:
        st.markdown(
            f"""<div class="opportunity-card">{escape(_localize_campaign_text(opportunity))}</div>""",
            unsafe_allow_html=True,
        )


def _text_panel(label: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="text-panel">
          <span>{escape(label)}</span>
          <p>{escape(_localize_campaign_text(text))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _details(report: WeeklyGrowthReport, expanded: bool = False) -> None:
    with st.expander("Tabelas e fontes", expanded=expanded):
        if report.rates:
            st.dataframe(
                pd.DataFrame([rate.model_dump() for rate in report.rates]),
                use_container_width=True,
                hide_index=True,
            )
        if report.channels:
            st.dataframe(
                pd.DataFrame([channel.model_dump() for channel in report.channels]),
                use_container_width=True,
                hide_index=True,
            )
        if report.campaigns:
            campaign_rows = []
            for campaign in report.campaigns:
                row = campaign.model_dump()
                row["name"] = _campaign_display_name(str(row["name"]))
                row["objective"] = _localize_campaign_text(str(row.get("objective") or ""))
                row["summary"] = _localize_campaign_text(str(row["summary"]))
                campaign_rows.append(row)
            st.dataframe(
                pd.DataFrame(campaign_rows),
                use_container_width=True,
                hide_index=True,
            )
        st.caption("Fontes")
        for source in report.sources:
            st.code(source)


def _channel_card(name: str, summary: str, change: float | None) -> None:
    status_class = _status_class(change)
    st.markdown(
        f"""
        <div class="list-card">
          <div>
            <strong>{escape(name)}</strong>
            <p>{escape(summary)}</p>
          </div>
          <span class="badge {status_class}">{escape(_change_label(change))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _revenue_bars(report: WeeklyGrowthReport, collection: ReportCollection | None = None) -> None:
    channel_rows = _channel_comparisons(report, collection)
    channels = [
        (str(channel["channel"]), float(channel["current"]), channel["change_pct"])
        for channel in channel_rows
    ]
    max_revenue = max((revenue for _, revenue, _ in channels), default=0)
    if max_revenue <= 0:
        st.info("Sem receita por canal para exibir.")
        return

    rows = []
    for name, revenue, change in sorted(channels, key=lambda item: item[1], reverse=True):
        width = max(5, round((revenue / max_revenue) * 100))
        tone = _status_class(change)
        rows.append(
            f'<div class="bar-row">'
            f'<div class="bar-label"><strong>{escape(name)}</strong><span>{_money(revenue)}</span></div>'
            f'<div class="bar-track"><div class="bar-fill {tone}" style="width:{width}%"></div></div>'
            f'<span class="bar-change {tone}">{escape(_change_label(change if isinstance(change, float) else None))}</span>'
            f"</div>"
        )

    st.markdown(
        f'<div class="chart-card">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )


def _imported_sources_list(sources: list[SourceConfig]) -> None:
    if not sources:
        st.info("Nenhuma fonte importada ainda.")
        return

    cards = []
    for source in sources:
        location = str(source.url or source.path or "")
        cards.append(
            f'<div class="import-source-card">'
            f'<span>{escape(source.type.value)}</span>'
            f'<strong>{escape(source.name)}</strong>'
            f'<small>{escape(location)}</small>'
            f"</div>"
        )
    st.markdown(f'<div class="import-source-grid">{"".join(cards)}</div>', unsafe_allow_html=True)

    if st.button("Limpar fontes importadas", use_container_width=True):
        _save_imported_sources([])
        st.success("Fontes importadas limpas.")
        st.rerun()


class DashboardPageActions:
    def kpi_row(self, report: WeeklyGrowthReport) -> None:
        _kpi_row(report)

    def comparison_strip(self, report: WeeklyGrowthReport, collection: ReportCollection) -> None:
        _comparison_strip(report, collection)

    def revenue_bars(
        self,
        report: WeeklyGrowthReport,
        collection: ReportCollection | None = None,
    ) -> None:
        _revenue_bars(report, collection)

    def risk_list(self, report: WeeklyGrowthReport, limit: int | None = None) -> None:
        _risk_list(report, limit)

    def executive_focus(self, report: WeeklyGrowthReport, collection: ReportCollection) -> None:
        _executive_focus(report, collection)

    def next_steps_panel(self, report: WeeklyGrowthReport, limit: int | None = None) -> None:
        _next_steps_panel(report, limit)

    def history_summary(self, reports: list[WeeklyGrowthReport]) -> None:
        _history_summary(reports)

    def history_timeline(
        self,
        reports: list[WeeklyGrowthReport],
        selected_report: WeeklyGrowthReport,
    ) -> None:
        _history_timeline(reports, selected_report)

    def report_revenue(self, report: WeeklyGrowthReport) -> float:
        return _report_revenue(report)

    def report_conversions(self, report: WeeklyGrowthReport) -> float:
        return _report_conversions(report)

    def report_roas(self, report: WeeklyGrowthReport) -> float:
        return _report_roas(report)

    def money(self, value: float) -> str:
        return _money(value)

    def number(self, value: float) -> str:
        return _number(value)

    def roas_benchmark_note(self) -> None:
        _roas_benchmark_note()

    def roas_tone(self, value: float) -> str:
        return _roas_tone(value)

    def roas_label(self, value: float) -> str:
        return _roas_label(value)

    def campaign_display_name(self, name: str) -> str:
        return _campaign_display_name(name)

    def localize_campaign_text(self, text: str) -> str:
        return _localize_campaign_text(text)

    def campaign_investment_context(
        self,
        name: str,
        channel: str,
        spend: float | None = None,
    ) -> str:
        return _campaign_investment_context(name, channel, spend)

    def channel_comparisons(
        self,
        report: WeeklyGrowthReport,
        collection: ReportCollection | None = None,
    ) -> list[dict[str, object]]:
        return _channel_comparisons(report, collection)

    def channel_diagnostic_grid(self, channels: list[dict[str, object]]) -> None:
        _channel_diagnostic_grid(channels)

    def channel_priority_action(self, channels: list[dict[str, object]]) -> None:
        _channel_priority_action(channels)

    def channel_card(self, name: str, summary: str, change: float | None) -> None:
        _channel_card(name, summary, change)

    def campaign_summary(self, campaigns) -> None:
        _campaign_summary(campaigns)

    def action_board(self, report: WeeklyGrowthReport) -> None:
        _action_board(report)

    def opportunities(self, report: WeeklyGrowthReport) -> None:
        _opportunities(report)

    def text_panel(self, label: str, text: str) -> None:
        _text_panel(label, text)

    def source_audit(self, report: WeeklyGrowthReport) -> None:
        _source_audit(report)

    def rates_audit(self, report: WeeklyGrowthReport) -> None:
        _rates_audit(report)

    def confidence_audit(self, report: WeeklyGrowthReport) -> None:
        _confidence_audit(report)

    def details(self, report: WeeklyGrowthReport, expanded: bool = False) -> None:
        _details(report, expanded)

    def load_imported_sources(self) -> list[SourceConfig]:
        return _load_imported_sources()

    def save_imported_sources(self, sources: list[SourceConfig]) -> None:
        _save_imported_sources(sources)

    def save_uploaded_source(self, uploaded_file) -> SourceConfig:
        return _save_uploaded_source(uploaded_file)

    def merge_sources(
        self,
        existing: list[SourceConfig],
        new_sources: list[SourceConfig],
    ) -> list[SourceConfig]:
        return _merge_sources(existing, new_sources)

    def imported_sources_list(self, sources: list[SourceConfig]) -> None:
        _imported_sources_list(sources)

