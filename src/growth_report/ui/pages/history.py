from __future__ import annotations

from html import escape

import streamlit as st

from growth_report.models import ReportCollection, WeeklyGrowthReport


def render(collection: ReportCollection, selected_report: WeeklyGrowthReport, ui) -> None:
    reports = sorted(collection.reports, key=lambda item: item.week_start)
    st.markdown('<div class="section-label">Histórico de relatórios</div>', unsafe_allow_html=True)
    ui.history_summary(reports)
    ui.history_timeline(reports, selected_report)

    st.markdown('<div class="section-label spacing-top">Relatórios salvos</div>', unsafe_allow_html=True)
    for report in reversed(reports):
        revenue = ui.report_revenue(report)
        conversions = ui.report_conversions(report)
        roas = ui.report_roas(report)
        roas_tone = ui.roas_tone(roas)
        roas_label = ui.roas_label(roas)
        selected = "selected" if report.report_id == selected_report.report_id else ""
        st.markdown(
            f'<div class="history-row {selected} {roas_tone}">'
            f'<div><strong>{report.week_start:%d/%m/%Y} - {report.week_end:%d/%m/%Y}</strong>'
            f'<p>{escape(ui.localize_campaign_text(report.executive_summary))}</p></div>'
            f'<span>{ui.money(revenue)}<small>receita</small></span>'
            f'<span>{ui.number(conversions)}<small>conversões</small></span>'
            f'<span class="roas-cell {roas_tone}">{roas:.2f}x<small>{escape(roas_label)}</small></span>'
            f"</div>",
            unsafe_allow_html=True,
        )
