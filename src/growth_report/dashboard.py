from __future__ import annotations

from html import escape

import streamlit as st

from growth_report.models import WeeklyGrowthReport
from growth_report.config import is_ai_configured
from growth_report.ui.components import DashboardPageActions
from growth_report.ui.formatters import localize_campaign_text
from growth_report.ui.page_router import NAV_LABELS, page_description, page_from_label, render_page
from growth_report.ui.report_store import DEFAULT_REPORTS_PATH, load_collection
from growth_report.ui.theme import apply_theme


APP_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="16" fill="#0F172A"/>
  <path d="M14 43h36" stroke="#38BDF8" stroke-width="4" stroke-linecap="round"/>
  <path d="M18 39l9-9 7 6 12-15" fill="none" stroke="#22C55E" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="18" cy="39" r="4" fill="#38BDF8"/>
  <circle cx="27" cy="30" r="4" fill="#38BDF8"/>
  <circle cx="34" cy="36" r="4" fill="#38BDF8"/>
  <circle cx="46" cy="21" r="5" fill="#22C55E"/>
</svg>
"""


def main() -> None:
    st.set_page_config(page_title="Growth AI Intelligence", page_icon=APP_ICON, layout="wide")

    # Theme mode state
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True

    apply_theme(dark=st.session_state.dark_mode)

    collection = load_collection(DEFAULT_REPORTS_PATH)
    if not collection.reports:
        st.info("Nenhum relatório salvo ainda.")
        return

    _render_sidebar_brand()

    # Navegação limpa
    selected_page = st.sidebar.radio("Navegação", NAV_LABELS, label_visibility="collapsed")
    page = page_from_label(selected_page)

    st.sidebar.markdown('<div style="height: 1px; background: var(--line); margin: 14px 0;"></div>', unsafe_allow_html=True)

    # Período compacto (sem emoji)
    report_options = {
        f"Semana: {report.week_start:%d/%m} – {report.week_end:%d/%m}": report
        for report in collection.reports
    }
    report_labels = list(report_options.keys())
    selected_label = st.sidebar.selectbox("Semana", options=report_labels, index=len(report_labels) - 1, label_visibility="collapsed")
    report = report_options[selected_label]

    st.sidebar.markdown('<div style="height: 1px; background: var(--line); margin: 14px 0;"></div>', unsafe_allow_html=True)

    # Toggle dark/light mode
    mode_label = "☀ Modo Claro" if st.session_state.dark_mode else "☾ Modo Escuro"
    if st.sidebar.button(mode_label, use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    _page_header(report, page)
    render_page(page, report, collection, DashboardPageActions())


def _render_sidebar_brand() -> None:
    ai_status = is_ai_configured()
    badge_text = "IA Ativa" if ai_status else "Modo Teste"
    badge_class = "brand-badge success" if ai_status else "brand-badge danger"
    node_color = "#22C55E" if ai_status else "#EF4444"
    
    st.sidebar.markdown(
        f"""
        <div class="brand-block">
          <div class="brand-mark" aria-label="Growth AI Intelligence">
            <svg class="brand-symbol" viewBox="0 0 64 64" role="img" aria-hidden="true">
              <rect class="symbol-bg" x="4" y="4" width="56" height="56" rx="15"></rect>
              <path class="symbol-grid" d="M16 44H50"></path>
              <path class="symbol-trend" d="M18 39L27 30L34 36L46 21"></path>
              <circle class="symbol-dot" cx="18" cy="39" r="3.8"></circle>
              <circle class="symbol-dot" cx="27" cy="30" r="3.8"></circle>
              <circle class="symbol-dot" cx="34" cy="36" r="3.8"></circle>
              <circle class="symbol-pulse" cx="46" cy="21" r="5.2" style="fill: {node_color};"></circle>
            </svg>
          </div>
          <div class="brand-wordmark" aria-label="Growth AI - Inteligência de Vendas">
            <span class="brand-name">Growth<span>AI</span></span>
            <span class="brand-tagline">Inteligência de Vendas</span>
          </div>
          <span class="{badge_class}">{badge_text}</span>
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
