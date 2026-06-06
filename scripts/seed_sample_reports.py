from __future__ import annotations

import json
from pathlib import Path


REPORTS_PATH = Path("data/reports/weekly_reports.json")


def campaign(
    name: str,
    channel: str,
    objective: str,
    spend: float,
    conversions: float,
    revenue: float,
    summary: str,
) -> dict:
    return {
        "name": name,
        "channel": channel,
        "objective": objective,
        "spend": spend,
        "conversions": conversions,
        "revenue": revenue,
        "roas": round(revenue / spend, 2) if spend else None,
        "summary": summary,
    }


def channel(
    name: str,
    current: float,
    previous: float,
    summary: str,
) -> dict:
    change = ((current - previous) / previous) * 100 if previous else 0
    return {
        "channel": name,
        "status": "up" if change >= 5 else "down" if change <= -5 else "stable",
        "current_value": current,
        "previous_value": previous,
        "change_pct": round(change, 1),
        "summary": summary,
    }


def report(
    report_id: str,
    week_start: str,
    week_end: str,
    generated_at: str,
    executive_summary: str,
    intro: str,
    performance: str,
    risks: list[str],
    rates: list[dict],
    opportunities: list[str],
    recommendations: list[dict],
    channels: list[dict],
    campaigns: list[dict],
    conclusion: str,
    source: str,
) -> dict:
    return {
        "report_id": report_id,
        "week_start": week_start,
        "week_end": week_end,
        "generated_at": generated_at,
        "executive_summary": executive_summary,
        "intro": intro,
        "performance": performance,
        "risks": risks,
        "rates": rates,
        "opportunities": opportunities,
        "recommendations": recommendations,
        "channels": channels,
        "campaigns": campaigns,
        "conclusion": conclusion,
        "sources": [source],
        "confidence_notes": [],
    }


def recommendation(priority: str, action: str, rationale: str, owner: str, impact: str) -> dict:
    return {
        "priority": priority,
        "action": action,
        "rationale": rationale,
        "owner_suggestion": owner,
        "expected_impact": impact,
    }


def rate(name: str, value: float, unit: str, context: str) -> dict:
    return {
        "name": name,
        "value": value,
        "unit": unit,
        "change_pct": None,
        "context": context,
    }


def main() -> None:
    existing = json.loads(REPORTS_PATH.read_text(encoding="utf-8"))
    current = next(
        (
            item for item in existing["reports"]
            if item.get("report_id") == "growth-2026-05-25-2026-05-31"
        ),
        existing["reports"][-1],
    )

    reports = [
        report(
            "growth-2026-05-11-2026-05-17",
            "2026-05-11",
            "2026-05-17",
            "2026-05-17T12:00:00Z",
            "A semana foi estável, com receita concentrada em Paid Search e Organic Search. Paid Social ainda sustentou volume, mas mostrou sinais de fadiga criativa. O foco recomendado é melhorar eficiência antes de aumentar orçamento.",
            "Relatório semanal de growth para 11 a 17 de maio de 2026.",
            "A receita total foi de R$ 16.500, com 244 conversões. O crescimento foi moderado e dependente de poucos canais, indicando necessidade de diversificar a aquisição.",
            [
                "Queda de 6.1% na receita do canal Email.",
                "ROAS abaixo de 3.0x na campanha 'Lookalike Trial'.",
            ],
            [
                rate("Revenue Growth", 4.8, "%", "Comparado à semana anterior"),
                rate("Conversions Growth", 3.4, "%", "Comparado à semana anterior"),
                rate("ROAS - Always On Search", 4.33, "x", "Campanha específica"),
            ],
            [
                "Revisar criativos de Paid Social antes de escalar orçamento.",
                "Criar novo fluxo de nutrição para recuperar o canal Email.",
                "Expandir pauta de conteúdo orgânico com temas de alta intenção.",
            ],
            [
                recommendation(
                    "high",
                    "Atualizar os criativos da campanha 'Lookalike Trial'.",
                    "A campanha ainda gera volume, mas ROAS e conversões mostram perda de eficiência.",
                    "Testar novas mensagens, audiências e prova social.",
                    "Recuperar 5-8% de eficiência em Paid Social.",
                ),
                recommendation(
                    "medium",
                    "Criar pauta de SEO para termos com intenção comercial.",
                    "Organic Search contribuiu sem mídia paga e pode crescer com baixo custo marginal.",
                    "Priorizar conteúdos de comparação e decisão.",
                    "Aumentar tráfego qualificado nas próximas 2-4 semanas.",
                ),
                recommendation(
                    "low",
                    "Monitorar queda do canal Email.",
                    "Email perdeu receita e conversões, mas ainda não representa risco crítico.",
                    "Revisar entregabilidade e segmentação.",
                    "Evitar piora no próximo ciclo.",
                ),
            ],
            [
                channel("Paid Search", 5200, 4900, "Crescimento moderado com boa eficiência em termos de marca."),
                channel("Paid Social", 5600, 5400, "Volume alto, mas com sinais de saturação em criativos."),
                channel("Organic Search", 2800, 2400, "Crescimento orgânico sustentado por conteúdo evergreen."),
                channel("Email", 1500, 1600, "Pequena queda por menor engajamento da base."),
                channel("Referral", 1400, 1450, "Canal estável, sem campanha relevante na semana."),
            ],
            [
                campaign("Always On Search", "Paid Search", "Demanda de fundo de funil", 1200, 72, 5200, "Campanha mais eficiente da semana em receita direta."),
                campaign("Lookalike Trial", "Paid Social", "Aquisição de novos usuários", 2100, 84, 5600, "Gera volume, mas precisa de novos criativos para proteger eficiência."),
                campaign("SEO Commercial Pages", "Organic Search", "Tráfego orgânico qualificado", 0, 38, 2800, "Receita orgânica sem investimento direto em mídia."),
                campaign("Newsletter Winback", "Email", "Reativação", 260, 25, 1500, "Resultado abaixo do histórico, exigindo revisão de segmentação."),
                campaign("Partner Mentions", "Referral", "Parcerias", 500, 25, 1400, "Resultado estável vindo de parceiros existentes."),
            ],
            "A semana fechou saudável, mas com dependência relevante de canais pagos. O próximo passo é corrigir eficiência antes de acelerar investimento.",
            "data/raw/sample_growth_week_2026_05_11.csv",
        ),
        report(
            "growth-2026-05-18-2026-05-24",
            "2026-05-18",
            "2026-05-24",
            "2026-05-24T12:00:00Z",
            "A semana acelerou em receita e conversões, puxada por Paid Search e Organic Search. Paid Social melhorou após ajustes, mas Email continuou abaixo do potencial. Recomendações priorizam escalar Search e recuperar Email.",
            "Relatório semanal de growth para 18 a 24 de maio de 2026.",
            "A receita total foi de R$ 17.900, com 262 conversões. Comparado à semana anterior, houve crescimento de 8.5% na receita e 7.4% nas conversões.",
            [
                "Queda de 5.9% na receita do canal Email.",
                "Referral ainda depende de poucos parceiros ativos.",
            ],
            [
                rate("Revenue Growth", 8.5, "%", "Comparado à semana anterior"),
                rate("Conversions Growth", 7.4, "%", "Comparado à semana anterior"),
                rate("ROAS - Always On Search", 4.5, "x", "Campanha específica"),
            ],
            [
                "Escalar Paid Search em grupos com ROAS acima de 4.0x.",
                "Reativar base de Email com oferta segmentada.",
                "Criar campanha dedicada para parceiros com maior potencial.",
            ],
            [
                recommendation(
                    "high",
                    "Aumentar orçamento de Paid Search em 15% nos grupos de maior ROAS.",
                    "O canal cresceu com eficiência e tem sinal claro para escala controlada.",
                    "Aplicar aumento apenas em termos e públicos com conversão consistente.",
                    "Capturar 6-10% de receita adicional mantendo ROAS saudável.",
                ),
                recommendation(
                    "medium",
                    "Reestruturar campanha de Email Nurture.",
                    "Email caiu novamente e precisa de nova segmentação para voltar a contribuir.",
                    "Separar leads frios, clientes inativos e trial abandonado.",
                    "Recuperar engajamento e reduzir risco de queda recorrente.",
                ),
                recommendation(
                    "low",
                    "Mapear parceiros com maior taxa de conversão.",
                    "Referral tem potencial, mas ainda é pequeno e concentrado.",
                    "Criar lista de parceiros prioritários.",
                    "Preparar base para campanha de referral na semana seguinte.",
                ),
            ],
            [
                channel("Paid Search", 5400, 5200, "Crescimento consistente com boa eficiência de mídia."),
                channel("Paid Social", 5900, 5600, "Melhora após ajustes de criativo e segmentação."),
                channel("Organic Search", 3100, 2800, "Conteúdo orgânico continuou ganhando tração."),
                channel("Email", 1600, 1700, "Canal ainda abaixo do esperado, com queda de engajamento."),
                channel("Referral", 1900, 1400, "Crescimento impulsionado por novas menções de parceiros."),
            ],
            [
                campaign("Always On Search", "Paid Search", "Demanda de fundo de funil", 1200, 78, 5400, "Boa eficiência e crescimento consistente em receita."),
                campaign("Lookalike Trial", "Paid Social", "Aquisição de novos usuários", 2000, 79, 5900, "Recuperação parcial após ajustes de campanha."),
                campaign("SEO Commercial Pages", "Organic Search", "Tráfego orgânico qualificado", 0, 43, 3100, "Crescimento orgânico com boa intenção comercial."),
                campaign("Newsletter Winback", "Email", "Reativação", 260, 27, 1600, "Ainda abaixo do potencial, apesar de leve melhora em conversões."),
                campaign("Partner Mentions", "Referral", "Parcerias", 520, 35, 1900, "Crescimento relevante por novas menções de parceiros."),
            ],
            "O crescimento melhorou, mas Email permanece como ponto de atenção. A próxima semana deve focar em escalar Paid Search com controle e preparar Referral.",
            "data/raw/sample_growth_week_2026_05_18.csv",
        ),
        current,
        report(
            "growth-2026-06-01-2026-06-07",
            "2026-06-01",
            "2026-06-07",
            "2026-06-07T12:00:00Z",
            "A semana fechou em queda forte, com reducao de receita e conversoes em todos os principais canais. Paid Social e Referral foram os pontos mais criticos, enquanto Paid Search ainda manteve algum volume, mas perdeu eficiencia. A prioridade e conter perda, revisar verba e corrigir campanhas antes de escalar novamente.",
            "Relatorio semanal de growth para 1 a 7 de junho de 2026, com queda geral de performance.",
            "A receita total caiu para R$ 13.500, com 205 conversoes. Comparado a semana anterior, houve queda de 34.5% na receita e 31.0% nas conversoes, indicando um ciclo de correcao necessario antes de novos aumentos de investimento.",
            [
                "Queda de 34.5% na receita total da semana.",
                "Queda de 31.0% nas conversoes totais.",
                "Referral perdeu 42.4% de receita apos fim da campanha 'Partner Webinar'.",
                "Paid Social segue com queda e ROAS abaixo do desejado.",
            ],
            [
                rate("Revenue Growth", -34.5, "%", "Comparado a semana anterior"),
                rate("Conversions Growth", -31.0, "%", "Comparado a semana anterior"),
                rate("ROAS - Lookalike Trial", 1.88, "x", "Campanha especifica"),
            ],
            [
                "Pausar aumento de verba em canais com queda ate entender a causa.",
                "Revisar criativos, segmentacao e landing page de Paid Social.",
                "Criar plano de recuperacao para Referral apos queda da campanha de parceiros.",
            ],
            [
                recommendation(
                    "high",
                    "Congelar expansao de budget em Paid Social e Referral por uma semana.",
                    "Os dois canais puxaram a maior parte da queda e precisam de diagnostico antes de receber mais investimento.",
                    "Redistribuir apenas verba essencial para campanhas com ROAS comprovado.",
                    "Evitar perda adicional enquanto o time corrige segmentacao, oferta e funil.",
                ),
                recommendation(
                    "high",
                    "Auditar a campanha 'Lookalike Trial' antes do proximo ciclo.",
                    "A campanha caiu em receita e eficiencia, com ROAS baixo para aquisicao paga.",
                    "Revisar criativos, publico, frequencia e taxa de conversao da landing page.",
                    "Recuperar eficiencia e reduzir desperdicio de midia.",
                ),
                recommendation(
                    "medium",
                    "Reativar pipeline de parceiros para recuperar Referral.",
                    "A queda em Referral mostra dependencia de uma campanha pontual.",
                    "Criar lista de parceiros ativos e uma nova agenda de co-marketing.",
                    "Reduzir dependencia de campanhas isoladas.",
                ),
                recommendation(
                    "low",
                    "Monitorar Organic Search sem alterar prioridade de conteudo.",
                    "O canal caiu, mas segue com custo baixo e pode recuperar com conteudos ja publicados.",
                    "Acompanhar paginas com maior perda de cliques.",
                    "Separar queda sazonal de problema estrutural.",
                ),
            ],
            [
                channel("Paid Search", 4200, 6200, "Queda relevante apos reducao de demanda em termos de marca e piora na taxa de conversao."),
                channel("Paid Social", 3200, 5100, "Continua em queda, com sinais de fadiga criativa e ROAS abaixo do alvo."),
                channel("Organic Search", 2800, 3900, "Perdeu receita na semana, mas segue como canal de menor custo direto."),
                channel("Email", 1400, 2100, "Queda de engajamento e menor resposta da base de reativacao."),
                channel("Referral", 1900, 3300, "Queda forte apos encerramento da campanha 'Partner Webinar'."),
            ],
            [
                campaign("Brand Protection", "Paid Search", "Geracao de Leads/Vendas", 1250, 61, 4200, "Ainda gera receita, mas perdeu volume e eficiencia frente a semana anterior."),
                campaign("Lookalike Trial", "Paid Social", "Aquisicao de Novos Clientes", 1700, 45, 3200, "ROAS baixo e queda de conversoes indicam necessidade de pausa e revisao."),
                campaign("Content Cluster SaaS", "Organic Search", "Brand Awareness/Trafego Organico", 0, 41, 2800, "Queda de receita, mas ainda contribui sem investimento direto em midia."),
                campaign("Nurture Reactivation", "Email", "Reativacao de Clientes", 250, 25, 1400, "Perda de engajamento e menor retorno da base reativada."),
                campaign("Partner Webinar", "Referral", "Geracao de Leads/Parcerias", 600, 33, 1900, "Fim do pico de campanha reduziu receita e conversoes do canal."),
            ],
            "A semana exige postura defensiva: entender a queda, proteger caixa de midia e corrigir os canais pagos antes de voltar a escalar. O dashboard deve destacar alertas, quedas por canal e decisoes prioritarias.",
            "data/raw/sample_growth_negative_2026_06_01.csv",
        ),
    ]

    REPORTS_PATH.write_text(
        json.dumps({"reports": reports}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
