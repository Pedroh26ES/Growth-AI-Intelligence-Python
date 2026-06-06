from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from typing import Protocol

from openai import OpenAI
from pydantic import ValidationError

from growth_report.dates import report_id_for
from growth_report.models import CollectedDocument, WeeklyGrowthReport


class ReportGenerationError(RuntimeError):
    pass


class ReportGenerator(Protocol):
    def generate(
        self,
        documents: list[CollectedDocument],
        week_start: date,
        week_end: date,
    ) -> WeeklyGrowthReport:
        ...


class OpenAIReportGenerator:
    def __init__(self, model: str, temperature: float = 0.2) -> None:
        if not os.getenv("OPENAI_API_KEY"):
            raise ReportGenerationError("OPENAI_API_KEY is not configured.")
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature

    def generate(
        self,
        documents: list[CollectedDocument],
        week_start: date,
        week_end: date,
    ) -> WeeklyGrowthReport:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": _system_prompt(),
                },
                {
                    "role": "user",
                    "content": _user_prompt(documents, week_start, week_end),
                },
            ],
            temperature=self.temperature,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "weekly_growth_report",
                    "strict": True,
                    "schema": WeeklyGrowthReport.model_json_schema(),
                }
            },
        )

        try:
            payload = json.loads(response.output_text)
            return WeeklyGrowthReport.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ReportGenerationError("OpenAI response did not match the report schema.") from exc


class GeminiReportGenerator:
    def __init__(self, model: str, temperature: float = 0.2) -> None:
        if not os.getenv("GEMINI_API_KEY"):
            raise ReportGenerationError("GEMINI_API_KEY is not configured.")

        from google import genai

        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = model
        self.temperature = temperature
        self.fallback_models = [
            item.strip()
            for item in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.0-flash-lite").split(",")
            if item.strip()
        ]

    def generate(
        self,
        documents: list[CollectedDocument],
        week_start: date,
        week_end: date,
    ) -> WeeklyGrowthReport:
        prompt = "\n\n".join(
            [
                _system_prompt(),
                "JSON schema esperado:",
                json.dumps(WeeklyGrowthReport.model_json_schema(), ensure_ascii=False),
                _user_prompt(documents, week_start, week_end),
            ]
        )
        last_error: Exception | None = None
        for model in _dedupe([self.model, *self.fallback_models]):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={
                        "temperature": self.temperature,
                        "response_mime_type": "application/json",
                    },
                )
                break
            except Exception as exc:
                last_error = exc
        else:
            raise ReportGenerationError("All Gemini models failed.") from last_error

        try:
            return WeeklyGrowthReport.model_validate_json(response.text)
        except ValidationError as exc:
            raise ReportGenerationError("Gemini response did not match the report schema.") from exc


class DryRunReportGenerator:
    def generate(
        self,
        documents: list[CollectedDocument],
        week_start: date,
        week_end: date,
    ) -> WeeklyGrowthReport:
        source_names = [document.source_name for document in documents]
        combined_text = "\n\n".join(document.text[:1200] for document in documents)
        fallback_summary = (
            "Relatório demonstrativo gerado em modo dry-run. Configure a chave da IA "
            "para obter uma análise real com IA."
        )
        if combined_text.strip():
            fallback_summary += f" Foram lidas {len(documents)} fonte(s): {', '.join(source_names)}."

        return WeeklyGrowthReport.model_validate(
            {
                "report_id": report_id_for(week_start, week_end),
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "executive_summary": fallback_summary,
                "intro": "Visão inicial baseada nas fontes coletadas no pipeline.",
                "performance": "Sem chamada de IA, os indicadores detalhados não foram inferidos.",
                "risks": ["Validar se todas as fontes oficiais estão configuradas e atualizadas."],
                "rates": [],
                "opportunities": ["Ativar a integração de IA para gerar recomendações específicas."],
                "recommendations": [
                    {
                        "priority": "medium",
                        "action": "Configurar a API key e executar o pipeline sem --dry-run.",
                        "rationale": "A análise final depende de interpretação estruturada dos dados.",
                        "owner_suggestion": "Growth Ops",
                        "expected_impact": "Relatórios semanais prontos antes da reunião de gestão.",
                    }
                ],
                "channels": [],
                "campaigns": [],
                "conclusion": "Modo dry-run concluído com sucesso.",
                "sources": source_names,
                "confidence_notes": [
                    "Este relatório é apenas uma validação técnica do pipeline.",
                    "Nenhum dado sensível foi enviado para a IA no modo dry-run.",
                ],
            }
        )


def _system_prompt() -> str:
    return (
        "Você é um analista sênior de growth marketing. Gere apenas um JSON válido "
        "seguindo exatamente o schema solicitado. Todo texto narrativo do JSON deve "
        "estar em português do Brasil, mesmo quando as fontes estiverem em outro idioma. "
        "Use nomes próprios, códigos internos e IDs oficiais originais quando fizer sentido, "
        "mas escreva nomes descritivos de canais, campanhas e métricas no formato "
        "Português (English), por exemplo Pesquisa Paga (Paid Search). Preserve acrônimos "
        "comuns como ROAS, SEO, CRM, LTV, CSV e PDF. Traduza também "
        "análises, riscos, oportunidades, recomendações, conclusões, notas e resumos para "
        "português do Brasil. Seja objetivo, executivo e acionável. "
        "Quando dados estiverem ausentes, registre a limitação em confidence_notes em vez "
        "de inventar números."
    )


def _user_prompt(
    documents: list[CollectedDocument],
    week_start: date,
    week_end: date,
) -> str:
    sections = []
    for document in documents:
        text = document.text[:18000]
        normalized_records = [
            record.model_dump(exclude_none=True) for record in document.normalized_records[:200]
        ]
        normalized_payload = json.dumps(normalized_records, ensure_ascii=False, indent=2)
        normalization_notes = "\n".join(f"- {note}" for note in document.normalization_notes)
        sections.append(
            "\n".join(
                [
                    f"Fonte: {document.source_name}",
                    f"Tipo: {document.source_type}",
                    f"URI: {document.uri}",
                    "Dados normalizados para o schema interno:",
                    normalized_payload if normalized_records else "[]",
                    "Notas de normalizacao:",
                    normalization_notes or "- Nenhuma nota.",
                    "Conteudo extraido:",
                    text,
                ]
            )
        )

    return (
        f"Período analisado: {week_start.isoformat()} a {week_end.isoformat()}.\n\n"
        "Idioma obrigatório de saída: português do Brasil para todos os campos textuais "
        "do relatório. Nomes descritivos de canais, campanhas e métricas devem ficar no "
        "formato Português (English), exceto se forem marcas, códigos internos ou IDs "
        "oficiais. Exemplos: Paid Search vira Pesquisa Paga (Paid Search), Revenue Growth "
        "vira Crescimento de Receita (Revenue Growth). Use exemplos realistas de growth, "
        "como Pesquisa de Marca Sempre Ativa (Always-on Brand Search), Lookalike de "
        "Clientes de Alto Valor (High-LTV Lookalike), Reativação CRM de Leads Inativos "
        "(CRM Reactivation), Páginas SEO de Alta Intenção (High-Intent SEO Pages) e "
        "Webinar de Co-marketing (Partner Webinar).\n\n"
        "Tarefa: extraia os principais números de growth, compare crescimento/queda "
        "quando houver base anterior, identifique campanhas fortes, riscos, "
        "oportunidades e recomendações práticas para a semana seguinte.\n\n"
        "Prioridade de leitura: use primeiro os blocos 'Dados normalizados para o schema "
        "interno'. Eles ja convertem colunas equivalentes como Cost/Investimento/Spend "
        "para spend, Conversions/Leads/Vendas para conversions e "
        "Revenue/Receita/Faturamento para revenue. Use o conteudo extraido apenas como "
        "contexto complementar ou para explicar limitacoes.\n\n"
        f"report_id obrigatorio: {report_id_for(week_start, week_end)}\n\n"
        "Fontes coletadas:\n"
        + "\n\n---\n\n".join(sections)
    )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items
