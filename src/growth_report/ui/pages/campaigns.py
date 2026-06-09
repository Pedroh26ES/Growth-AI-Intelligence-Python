from __future__ import annotations

from html import escape

import streamlit as st

from growth_report.models import WeeklyGrowthReport


def render(report: WeeklyGrowthReport, ui) -> None:
    st.markdown('<div class="section-label">Análise de campanhas</div>', unsafe_allow_html=True)
    
    with st.expander("❓ Como ler esta seção (Métricas & Definições)", expanded=False):
        st.markdown(
            """
            <div class="text-panel" style="margin-bottom: 0rem; border-left: 3px solid var(--primary); background: transparent; border-top: none; border-right: none; border-bottom: none; box-shadow: none; padding: 0.2rem 0.5rem;">
              <span>Definição de Campanhas</span>
              <p>
                Esta área detalha o desempenho individual das <strong>campanhas e ações específicas de marketing</strong> executadas em cada canal. 
                Diferente dos "Canais" (que agrupam todo o tráfego de uma plataforma), as <strong>Campanhas</strong> representam iniciativas concretas, como anúncios de proteção de marca no Google Ads, fluxos automatizados de e-mail marketing (CRM), campanhas de público semelhante (lookalike) em redes sociais, ou clusters específicos de páginas SEO.
              </p>
              <p style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--muted);">
                💡 <strong>Entenda as métricas:</strong> <strong>Receita</strong> é o valor total gerado em vendas; 
                <strong>Investimento</strong> é o orçamento de mídia direta consumido; e 
                <strong>ROAS</strong> (Retorno sobre Investimento em Anúncios) mede a eficiência de cada Real investido (ex: 5.00x significa que cada R$ 1 investido em anúncios gerou R$ 5 de receita). Campanhas sem investimento direto (como busca orgânica/SEO) não possuem cálculo de ROAS.
              </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    if not report.campaigns:
        st.warning("Sem campanhas.")
        return

    channel_options = ["Todos", *sorted({campaign.channel for campaign in report.campaigns})]
    filter_col, perf_col, sort_col = st.columns([1, 1, 1])
    selected_channel = filter_col.selectbox("Canal", channel_options)
    selected_perf = perf_col.selectbox("Desempenho", ["Todos", "Positivo (Bom ROAS)", "Negativo/Crítico"])
    selected_sort = sort_col.selectbox("Ordenar por", ["ROAS", "Receita", "Conversões"])

    def _matches_perf(campaign) -> bool:
        if selected_perf == "Todos":
            return True
        tone = ui.roas_tone(campaign.roas or 0)
        is_positive = tone in ("roi-excellent", "roi-good")
        return is_positive if selected_perf.startswith("Positivo") else not is_positive

    visible_campaigns = [
        campaign
        for campaign in report.campaigns
        if (selected_channel == "Todos" or campaign.channel == selected_channel)
        and _matches_perf(campaign)
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
            f"ROAS: {campaign.roas:.2f}x"
            if campaign.roas
            else "Sem ROAS"
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
