from __future__ import annotations

from html import escape

import streamlit as st

from growth_report.models import WeeklyGrowthReport


def render(report: WeeklyGrowthReport, ui) -> None:
    st.markdown('<div class="section-label">Análise de campanhas</div>', unsafe_allow_html=True)
    if not report.campaigns:
        st.warning("Sem campanhas.")
        return

    channel_options = ["Todos", *sorted({campaign.channel for campaign in report.campaigns})]
    filter_col, sort_col = st.columns([1, 1])
    selected_channel = filter_col.selectbox("Canal", channel_options)
    selected_sort = sort_col.selectbox("Ordenar por", ["ROAS", "Receita", "Conversões"])

    visible_campaigns = [
        campaign
        for campaign in report.campaigns
        if selected_channel == "Todos" or campaign.channel == selected_channel
    ]
    sort_key = {
        "ROAS": lambda campaign: (campaign.roas or 0, campaign.revenue or 0),
        "Receita": lambda campaign: (campaign.revenue or 0, campaign.roas or 0),
        "Conversões": lambda campaign: (campaign.conversions or 0, campaign.revenue or 0),
    }[selected_sort]

    campaigns = sorted(visible_campaigns, key=sort_key, reverse=True)
    if not campaigns:
        st.warning("Nenhuma campanha encontrada para esse filtro.")
        return

    ui.campaign_summary(campaigns)
    ui.roas_benchmark_note()

    st.markdown('<div class="section-label spacing-top">Ranking de campanhas</div>', unsafe_allow_html=True)
    for campaign in campaigns:
        roas_value = campaign.roas or 0
        roas_tone = ui.roas_tone(roas_value)
        roas_label = ui.roas_label(roas_value)
        campaign_name = ui.campaign_display_name(campaign.name)
        campaign_summary = ui.localize_campaign_text(campaign.summary)
        investment_context = ui.campaign_investment_context(
            campaign_name,
            campaign.channel,
            campaign.spend,
        )
        roas = (
            f"ROAS(Return on Ad Spend): {campaign.roas:.2f}x"
            if campaign.roas
            else "sem ROAS(Return on Ad Spend)"
        )
        st.markdown(
            f"""
            <div class="list-card campaign-card {roas_tone}">
              <div>
                <strong>{escape(campaign_name)}</strong>
                <p>{escape(campaign_summary)}</p>
                <div class="campaign-context">
                  <span>Onde entra o investimento</span>
                  <small>{escape(investment_context)}</small>
                </div>
              </div>
              <span class="campaign-metric">
                <small>{escape(campaign.channel)} | {ui.money(campaign.revenue or 0)}</small>
                <b class="roas-pill {roas_tone}">{escape(roas)}</b>
                <em>{escape(roas_label)}</em>
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
