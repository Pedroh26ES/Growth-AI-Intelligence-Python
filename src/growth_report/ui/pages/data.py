from __future__ import annotations

import streamlit as st

from growth_report.models import WeeklyGrowthReport


def render(report: WeeklyGrowthReport, ui) -> None:
    st.markdown('<div class="section-label">Leitura completa</div>', unsafe_allow_html=True)
    ui.text_panel("Resumo executivo", report.executive_summary)
    ui.text_panel("Performance", report.performance)
    ui.text_panel("Conclusão", report.conclusion)

    st.markdown('<div class="section-label spacing-top">Critério de leitura</div>', unsafe_allow_html=True)
    ui.roas_benchmark_note()

    st.markdown('<div class="section-label spacing-top">Dados de suporte</div>', unsafe_allow_html=True)
    left, right = st.columns([1.15, 1])
    with left:
        ui.source_audit(report)
    with right:
        ui.rates_audit(report)
        ui.confidence_audit(report)

    st.markdown('<div class="section-label spacing-top">Tabelas detalhadas</div>', unsafe_allow_html=True)
    ui.details(report, expanded=False)
