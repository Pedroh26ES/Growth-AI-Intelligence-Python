from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


THEME_CSS_PATH = Path(__file__).with_name("theme.css")


def apply_theme(dark: bool = True) -> None:
    css = THEME_CSS_PATH.read_text(encoding="utf-8").lstrip("\ufeff")
    theme_class = "dark-mode" if dark else "light-mode"
    
    # Inject CSS
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    
    # Inject JS to toggle the theme class in the parent document.
    js = f"""
    <script>
        const parentDoc = window.parent.document;
        const themeClass = "{theme_class}";
        const applyThemeClass = () => {{
            [parentDoc.documentElement, parentDoc.body].forEach((node) => {{
                if (!node) return;
                node.classList.remove("dark-mode", "light-mode");
                node.classList.add(themeClass);
                node.dataset.theme = themeClass.replace("-mode", "");
            }});
        }};
        applyThemeClass();
        window.requestAnimationFrame(applyThemeClass);
    </script>
    """
    components.html(js, height=0, width=0)
