from __future__ import annotations

from html import escape

import streamlit as st

from growth_report.models import WeeklyGrowthReport
from growth_report.ui.components import DashboardPageActions
from growth_report.ui.formatters import localize_campaign_text
from growth_report.ui.page_router import NAV_LABELS, page_description, page_from_label, render_page
from growth_report.ui.report_store import DEFAULT_REPORTS_PATH, load_collection
from growth_report.ui.theme import apply_theme


def main() -> None:
    st.set_page_config(page_title="Growth AI Intelligence", layout="wide")
    apply_theme()

    collection = load_collection(DEFAULT_REPORTS_PATH)
    if not collection.reports:
        st.info("Nenhum relatório salvo ainda.")
        return

    _render_sidebar_brand()
    _render_sidebar_section("Navegação")
    selected_page = st.sidebar.radio("Navegação", NAV_LABELS, label_visibility="collapsed")
    page = page_from_label(selected_page)
    st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    _render_sidebar_section("Período")

    report_options = {
        f"{report.week_start:%d/%m/%Y} - {report.week_end:%d/%m/%Y}": report
        for report in collection.reports
    }
    report_labels = list(report_options.keys())
    selected_label = st.sidebar.selectbox("Semana", options=report_labels, index=len(report_labels) - 1)
    report = report_options[selected_label]

    _render_sidebar_status(len(collection.reports))
    _render_sidebar_footer()
    _page_header(report, page)
    render_page(page, report, collection, DashboardPageActions())


def _render_sidebar_brand() -> None:
    st.sidebar.markdown(
        """
        <div class="brand-block">
          <div class="brand-mark" aria-label="Growth AI Intelligence logo">
            <span class="logo-orbit"></span>
            <span class="logo-bars">
              <i></i><i></i><i></i>
            </span>
            <span class="logo-node"></span>
          </div>
          <div>
            <strong>Growth AI Intelligence</strong>
            <small>Weekly growth report</small>
          </div>
          <span class="brand-badge">Ativo</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar_section(label: str) -> None:
    st.sidebar.markdown(
        f'<div class="sidebar-section-label">{escape(label)}</div>',
        unsafe_allow_html=True,
    )


def _render_sidebar_status(report_count: int) -> None:
    st.sidebar.markdown(
        f"""
        <div class="sidebar-profile">
          <span>Arquivo ativo</span>
          <strong>{report_count} relatório(s)</strong>
          <small>{DEFAULT_REPORTS_PATH}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar_footer() -> None:
    st.sidebar.markdown(
        """
        <div class="sidebar-footer">
          <strong>Atualização semanal</strong>
          <small>Segunda-feira, 06:00</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _page_header(report: WeeklyGrowthReport, page: str) -> None:
    description = localize_campaign_text(page_description(page, report.intro))
    st.markdown(
        f"""
        <div class="page-title">
          <div>
            <p class="breadcrumb">HOME &gt; {escape(page).upper()}</p>
            <h1>{escape(page)}</h1>
            <p class="header-summary">{escape(description)}</p>
          </div>
          <div class="generated">
            {report.week_start:%d/%m/%Y} - {report.week_end:%d/%m/%Y}<br>
            Gerado em {report.generated_at:%d/%m/%Y %H:%M}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
