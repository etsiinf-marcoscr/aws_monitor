import streamlit as st


def render_refresh_button():

    st.markdown(
        """
        <style>
            /* Ancla el contenedor del botón al fondo del sidebar */
            [data-testid="refresh-float-btn"] {
                position: fixed !important;
                bottom: 24px !important;
                left: 0 !important;
                width: 244px !important;   /* ancho estándar del sidebar de Streamlit */
                padding: 0 1rem !important;
                z-index: 99999 !important;
            }

            [data-testid="refresh-float-btn"] > button {
                width: 100% !important;
                border-radius: 8px !important;
                background: #ffffff12 !important;
                color: white !important;
                border: 1px solid #ffffff25 !important;
                transition: background 0.2s !important;
            }

            [data-testid="refresh-float-btn"] > button:hover {
                background: #ffffff28 !important;
                border-color: #ffffff50 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        clicked = st.button(
            "↺  Actualizar",
            key="refresh-float-btn",
            help="Vuelve a cargar los datos de esta sección",
            width='stretch',
        )

    if clicked:
        st.rerun()