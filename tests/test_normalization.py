import pandas as pd

from growth_report.models import CollectedDocument, SourceType
from growth_report.normalization import normalize_collected_document, normalize_dataframe


def test_normalize_google_ads_csv_shape_with_english_columns() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "Campaign": "Brand Protection",
                "Cost": "R$ 1.200,00",
                "Clicks": 540,
                "Conversions": 88,
                "Leads": 310,
                "Revenue": "R$ 6.200,00",
            }
        ]
    )

    records, notes = normalize_dataframe(
        dataframe,
        source_name="Google Ads Export",
        source_kind="google_ads",
    )

    assert len(records) == 1
    assert records[0].campaign == "Brand Protection"
    assert records[0].channel == "Pesquisa Paga (Paid Search)"
    assert records[0].spend == 1200
    assert records[0].clicks == 540
    assert records[0].conversions == 88
    assert records[0].revenue == 6200
    assert "1 registro(s) normalizado(s)" in notes[-1]


def test_normalize_crm_excel_shape_with_portuguese_columns() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "Nome da campanha": "Reativacao CRM",
                "Investimento": 250,
                "Leads": 39,
                "Receita": 2100,
            }
        ]
    )

    records, _ = normalize_dataframe(
        dataframe,
        source_name="CRM semanal",
        source_kind="crm",
    )

    assert records[0].campaign == "Reativacao CRM"
    assert records[0].channel == "CRM"
    assert records[0].spend == 250
    assert records[0].conversions == 39
    assert records[0].revenue == 2100


def test_normalize_pdf_like_text_extracts_campaign_metric_pattern() -> None:
    document = CollectedDocument(
        source_name="PDF executivo",
        source_type=SourceType.PDF_FILE,
        uri="report.pdf",
        content_type="application/pdf",
        text="Campanha Protecao de Marca teve 120 leads e R$ 4.500 de receita.",
        metadata={"tags": "pdf,marketing"},
    )

    normalized = normalize_collected_document(document)

    assert len(normalized.normalized_records) == 1
    record = normalized.normalized_records[0]
    assert record.campaign == "Protecao de Marca"
    assert record.conversions == 120
    assert record.revenue == 4500
    assert record.source_kind == "pdf_report"
