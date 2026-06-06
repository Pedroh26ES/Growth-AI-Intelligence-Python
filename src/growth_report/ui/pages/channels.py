from __future__ import annotations

import streamlit as st

from growth_report.models import ReportCollection, WeeklyGrowthReport


def render(report: WeeklyGrowthReport, collection: ReportCollection, ui) -> None:
    st.markdown('<div class="section-label">Diagnóstico por canal</div>', unsafe_allow_html=True)
    if not report.channels:
        st.warning("Sem dados de canais.")
        return

    channel_rows = ui.channel_comparisons(report, collection)
    st.markdown(
        '<div class="channel-note">'
        '<strong>Como ler:</strong> “Semana anterior” usa o relatório imediatamente anterior '
        'por data. “Peso na receita” mostra quanto o canal representa da receita total '
        'da semana selecionada.'
        '</div>',
        unsafe_allow_html=True,
    )
    ui.channel_diagnostic_grid(channel_rows)

    st.markdown('<div class="section-label spacing-top">Decisão recomendada</div>', unsafe_allow_html=True)
    ui.channel_priority_action(channel_rows)
