from __future__ import annotations

import streamlit as st

from growth_report.models import ReportCollection, WeeklyGrowthReport


def render(report: WeeklyGrowthReport, collection: ReportCollection, ui) -> None:
    ui.kpi_row(report)
    ui.roas_benchmark_note()
    ui.comparison_strip(report, collection)

    left, right = st.columns([1.35, .9])
    with left:
        st.markdown('<div class="section-label">Receita por canal</div>', unsafe_allow_html=True)
        ui.revenue_bars(report, collection)
        ui.risk_list(report, limit=2)
    with right:
        ui.executive_focus(report, collection)

    ui.next_steps_panel(report, limit=3)
