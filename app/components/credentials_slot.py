import os

import streamlit as st

from config import AWS_REGION, _env_bool


def _initial_value(session_key, env_name, default_value=""):
    """Recupera un valor inicial priorizando lo guardado en la sesion actual."""
    session_value = st.session_state.get(session_key)

    if session_value:
        return session_value

    return os.getenv(env_name, default_value)


def _ensure_mock_mode_initialized():
    """Inicializa mock_mode en session_state si todavia no existe."""
    if "mock_mode" not in st.session_state:
        st.session_state["mock_mode"] = _env_bool("MOCK_MODE", False)


def _sync_mock_mode_from_widget():
    """Sincroniza el valor del toggle con la clave interna usada por la app."""
    st.session_state["mock_mode"] = st.session_state["mock_mode_control"]


def _reset_credentials_to_env():
    """Restaura credenciales y region a los valores definidos en .env."""
    st.session_state["mock_mode"] = _env_bool("MOCK_MODE", False)
    st.session_state.pop("mock_mode_control", None)

    st.session_state["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID", "")
    st.session_state["aws_access_key_id_input"] = st.session_state["aws_access_key_id"]

    st.session_state["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    st.session_state["aws_secret_access_key_input"] = st.session_state["aws_secret_access_key"]

    st.session_state["aws_session_token"] = os.getenv("AWS_SESSION_TOKEN", "")
    st.session_state["aws_session_token_input"] = st.session_state["aws_session_token"]

    st.session_state["aws_region"] = os.getenv("AWS_DEFAULT_REGION", AWS_REGION)
    st.session_state["aws_region_input"] = st.session_state["aws_region"]


def render_aws_credentials_panel():
    """Pinta el panel lateral para configurar credenciales AWS durante la sesion."""
    _ensure_mock_mode_initialized()
    st.session_state["mock_mode_control"] = st.session_state["mock_mode"]

    if st.session_state["mock_mode"]:
        st.warning("⚠️ Modo simulación activo, se están usando datos simulados que no provienen de Amazon Web Services (AWS).")

    with st.sidebar.expander("👤 Credenciales AWS", expanded=False):
        st.caption("Los valores guardados aquí sobreescriben los del .env durante esta sesión.")

        st.toggle(
            "Modo simulación",
            key="mock_mode_control",
            on_change=_sync_mock_mode_from_widget,
        )

        with st.form("aws_credentials_form", clear_on_submit=False):
            access_key = st.text_input(
                "Access key ID",
                value=_initial_value("aws_access_key_id", "AWS_ACCESS_KEY_ID"),
                key="aws_access_key_id_input",
            )

            secret_key = st.text_input(
                "Secret access key",
                value=_initial_value("aws_secret_access_key", "AWS_SECRET_ACCESS_KEY"),
                key="aws_secret_access_key_input",
                type="password",
            )

            session_token = st.text_input(
                "Session token (opcional)",
                value=_initial_value("aws_session_token", "AWS_SESSION_TOKEN"),
                key="aws_session_token_input",
                type="password",
            )

            region = st.text_input(
                "Region",
                value=_initial_value("aws_region", "AWS_DEFAULT_REGION", AWS_REGION),
                key="aws_region_input",
            )

            submitted = st.form_submit_button("Guardar")

        if submitted:
            st.session_state["aws_access_key_id"] = access_key.strip()
            st.session_state["aws_secret_access_key"] = secret_key.strip()
            st.session_state["aws_session_token"] = session_token.strip()
            st.session_state["aws_region"] = region.strip() or AWS_REGION
            st.success("Credenciales AWS actualizadas para esta sesión.")
            st.rerun()

        st.button(
            "Restablecer valores del .env",
            key="aws_credentials_reset",
            on_click=_reset_credentials_to_env,
        )