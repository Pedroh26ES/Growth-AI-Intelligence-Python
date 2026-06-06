from __future__ import annotations

from pathlib import Path

import streamlit as st


THEME_CSS_PATH = Path(__file__).with_name("theme.css")


def apply_theme() -> None:
    css = THEME_CSS_PATH.read_text(encoding="utf-8").lstrip("\ufeff")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
