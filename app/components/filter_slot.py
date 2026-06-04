"""
filter_slot.py
Sidebar global que agrupa el panel de credenciales AWS y el filtro por etiquetas.
"""

import streamlit as st
from components.credentials_slot import render_aws_credentials_panel
from utils.tag_filter import set_tag_filter, clear_tag_filter, get_tag_filter
from config import get_mock_mode


# Claves de tag frecuentes en arquitecturas AWS
_SUGGESTED_TAG_KEYS = [
    "Stack",
    "environment",
]


def render_tag_filter_panel() -> None:
    """Pinta el panel de filtrado por etiquetas en el sidebar."""
    with st.sidebar.expander("🏷️ Filtro por etiqueta", expanded=False):

        if get_mock_mode():
            st.info("El filtro no aplica en modo simulación.")
            return

        current = get_tag_filter()

        if current:
            st.success(f"**{current['key']}** = `{current['value']}`")
            if st.button("✕ Quitar filtro", width='stretch'):
                clear_tag_filter()
                st.rerun()
            st.divider()

        tag_key = st.selectbox(
            "Clave de etiqueta",
            options=[""] + _SUGGESTED_TAG_KEYS + ["Otra (escribir)..."],
            index=0,
        )

        if tag_key == "Otra (escribir)...":
            tag_key = st.text_input(
                "Escribe la clave",
                placeholder="ej: tagKey, env, awstag",
            )

        tag_value = st.text_input(
            "Valor de etiqueta",
            placeholder="ej: arch1, prod, backend",
            disabled=not tag_key or tag_key == "",
        )

        if st.button(
            "Aplicar filtro",
            width='stretch',
            disabled=not tag_key or not tag_value,
            type="primary",
        ):
            set_tag_filter(tag_key, tag_value)
            st.rerun()