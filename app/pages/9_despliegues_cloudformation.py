import streamlit as st


from aws.cloudformation import (
    get_stacks_dataframe,
    get_stack_overview,
    get_stack_resources_dataframe,
    get_stack_template,
    get_stack_events_dataframe,
)
from utils.tag_filter import is_filter_active
from config import get_mock_mode

st.set_page_config(
    page_title="CloudFormation",
    layout="wide"
)

if is_filter_active() and not get_mock_mode():
    st.warning(
        "El filtro por etiqueta no aplica en CloudFormation. "
        "Es un servicio global de cuenta independiente de los stacks desplegados.",
        icon="⚠️",
    )

st.title("Despliegues (Stacks) en CloudFormation")

stacks = get_stacks_dataframe()

if stacks.empty:
    st.info("No se encontraron stacks de CloudFormation en esta cuenta.")

else:
    st.subheader("Listado de stacks")
    st.dataframe(
        stacks,
        width='stretch'
    )

    selected_stack = st.selectbox(
        "Selecciona un stack",
        stacks["Nombre del despliegue"]
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "Resumen",
        "Recursos",
        "Template",
        "Eventos"
    ])

    with tab1:
        overview = get_stack_overview(selected_stack)
        if not overview:
            st.info("No se pudo cargar el resumen del stack.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Estado", overview.get("Estado", "-"))
            col2.metric("Drift", overview.get("Estado de drift", "-"))
            col3.metric("Protección eliminación", "Sí" if overview.get("Protección ante eliminación") else "No")

            st.write(f"**Descripción:** {overview.get('Descripción', '-') or '-'}")
            st.write(f"**Creado:** {overview.get('Fecha de creación', '-')}")
            st.write(f"**Última actualización:** {overview.get('Fecha de última actualización', '-')}")

            tags = overview.get("Tags", [])
            outputs = overview.get("Outputs", [])

            st.write("**Etiquetas**")
            if tags:
                st.dataframe(tags, width='stretch')
            else:
                st.info("Este stack no tiene etiquetas.")

            st.write("**Salidas (Outputs)**")
            if outputs:
                st.dataframe(outputs, width='stretch')
            else:
                st.info("Este stack no tiene salidas definidas.")

    with tab2:
        resources_df = get_stack_resources_dataframe(selected_stack)
        if resources_df.empty:
            st.info("No se encontraron recursos para este stack.")
        else:
            st.dataframe(resources_df, width='stretch')

    with tab3:
        template_text = get_stack_template(selected_stack)
        if template_text.strip():
            st.code(template_text, language="yaml")
        else:
            st.info("No se pudo recuperar el template de este stack.")

    with tab4:
        events_df = get_stack_events_dataframe(selected_stack)
        if events_df.empty:
            st.info("No se encontraron eventos recientes para este stack.")
        else:
            st.dataframe(events_df, width='stretch')
