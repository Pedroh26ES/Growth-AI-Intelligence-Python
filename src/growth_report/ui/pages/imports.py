from __future__ import annotations

from html import escape

import streamlit as st

from growth_report.config import load_config
from growth_report.models import SourceConfig, SourceType
from growth_report.pipeline import run_pipeline


def render(ui) -> None:
    sources = ui.load_imported_sources()

    upload_tab, sheet_tab, run_tab = st.tabs(["Arquivos", "Google Sheets", "Processar"])

    with upload_tab:
        _step_card(
            "1",
            "Enviar arquivos",
            "Use esta opção para relatórios em PDF, bases CSV ou planilhas Excel exportadas pelo time.",
        )
        uploaded_files = st.file_uploader(
            "PDF, CSV ou Excel",
            type=["pdf", "csv", "xlsx", "xls"],
            accept_multiple_files=True,
            help="Envie relatórios PDF, bases CSV ou planilhas Excel para alimentar a IA.",
        )
        if uploaded_files:
            _selected_files(uploaded_files)

        if st.button("Salvar arquivos importados", use_container_width=True):
            if not uploaded_files:
                st.warning("Selecione pelo menos um arquivo.")
            else:
                saved_sources = [
                    ui.save_uploaded_source(uploaded_file)
                    for uploaded_file in uploaded_files
                ]
                sources = ui.merge_sources(sources, saved_sources)
                ui.save_imported_sources(sources)
                st.success(f"{len(saved_sources)} fonte(s) salva(s).")

    with sheet_tab:
        _step_card(
            "2",
            "Conectar Google Sheets",
            "Cole o link de uma planilha pública ou publicada como CSV para manter os dados sempre atualizáveis.",
        )
        sheet_name = st.text_input("Nome da fonte", value="Google Sheets Growth")
        sheet_url = st.text_input(
            "Link da planilha",
            placeholder="https://docs.google.com/spreadsheets/d/ID_DA_PLANILHA/edit#gid=0",
        )
        st.caption("A planilha precisa estar pública para leitura ou publicada com exportação CSV disponível.")

        if st.button("Salvar Google Sheets", use_container_width=True):
            if not sheet_url.strip():
                st.warning("Cole o link do Google Sheets.")
            else:
                source = SourceConfig(
                    name=sheet_name.strip() or "Google Sheets Growth",
                    type=SourceType.GOOGLE_SHEETS_URL,
                    url=sheet_url.strip(),
                    enabled=True,
                    tags=["google-sheets", "imported"],
                )
                sources = ui.merge_sources(sources, [source])
                ui.save_imported_sources(sources)
                st.success("Google Sheets salvo como fonte.")

    with run_tab:
        _step_card(
            "3",
            "Gerar relatório",
            "Revise as fontes importadas e rode o pipeline para criar uma nova leitura semanal no dashboard.",
        )
        sources = ui.load_imported_sources()
        ui.imported_sources_list(sources)

        dry_run = st.checkbox("Modo teste sem IA", value=False)
        _run_status(sources, dry_run)

        if st.button("Gerar relatório com fontes importadas", use_container_width=True):
            if not sources:
                st.warning("Importe pelo menos uma fonte antes de gerar o relatório.")
            else:
                try:
                    config = load_config()
                    config.sources = sources
                    report = run_pipeline(config, dry_run=dry_run)
                    st.success(f"Relatório gerado: {report.report_id}. Recarregue a Home para ver.")
                except Exception as exc:
                    st.error(f"Não foi possível gerar o relatório: {exc}")


def _step_card(step: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="import-step-card">
          <span>{escape(step)}</span>
          <div>
            <strong>{escape(title)}</strong>
            <p>{escape(body)}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _selected_files(uploaded_files) -> None:
    items = "".join(
        f"<li>{escape(uploaded_file.name)}</li>"
        for uploaded_file in uploaded_files
    )
    st.markdown(
        f'<div class="selected-files"><strong>Arquivos selecionados</strong><ul>{items}</ul></div>',
        unsafe_allow_html=True,
    )


def _run_status(sources: list[SourceConfig], dry_run: bool) -> None:
    mode = "teste sem IA" if dry_run else "IA ativa"
    tone = "neutral" if dry_run else "ready"
    st.markdown(
        f"""
        <div class="import-run-status {tone}">
          <span>{len(sources)} fonte(s)</span>
          <strong>{escape(mode)}</strong>
          <small>O relatório será salvo no histórico após o processamento.</small>
        </div>
        """,
        unsafe_allow_html=True,
    )
