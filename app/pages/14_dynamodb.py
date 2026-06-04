import streamlit as st


from aws.dynamodb import (
    get_tables_dataframe,
    get_read_throughput_metrics,
    get_write_throughput_metrics,
    get_throttled_requests_metrics
)
from utils.tag_filter import get_tag_filter

st.set_page_config(
    page_title="DynamoDB",
    layout="wide"
)

st.title("DynamoDB - Tablas")

tables_df = get_tables_dataframe()

if tables_df.empty:
    tag_filter = get_tag_filter()
    if tag_filter:
        all_tables_df = get_tables_dataframe(apply_tag_filter=False)
        if all_tables_df.empty:
            st.info("No se encontraron tablas DynamoDB para monitorizar.")
        else:
            st.info(
                f"No se encontraron tablas DynamoDB con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
    else:
        st.info("No se encontraron tablas DynamoDB para monitorizar.")
    st.stop()

st.subheader("Tablas de Base de Datos")
st.dataframe(tables_df, width="stretch")

selected_table = st.selectbox(
    "Selecciona una tabla",
    tables_df["Nombre de Tabla"]
)

try:
    tab_read, tab_write, tab_throttled = st.tabs([
        "% de Lectura",
        "% de escritura",
        "Conexiones"
    ])

    with tab_read:
        st.subheader("% de Lectura Consumida (última hora)")
        df = get_read_throughput_metrics(selected_table)
        if not df.empty:
            st.line_chart(df.set_index("instante")["% de Lectura"])
        else:
            st.info("No hay datos disponibles")

    with tab_write:
        st.subheader("% de escritura Consumida (última hora)")
        df = get_write_throughput_metrics(selected_table)
        if not df.empty:
            st.line_chart(df.set_index("instante")["% de escritura"])
        else:
            st.info("No hay datos disponibles")

    with tab_throttled:
        st.subheader("Conexiones (última hora)")
        df = get_throttled_requests_metrics(selected_table)
        if not df.empty:
            st.line_chart(df.set_index("instante")["Conexiones"])
        else:
            st.info("No hay datos disponibles")

except Exception:
    st.subheader("% de Lectura Consumida (última hora)")
    df = get_read_throughput_metrics(selected_table)
    if not df.empty:
        st.line_chart(df.set_index("instante")["% de Lectura"])
    else:
        st.info("No hay datos disponibles")

    st.subheader("% de escritura Consumida (última hora)")
    df = get_write_throughput_metrics(selected_table)
    if not df.empty:
        st.line_chart(df.set_index("instante")["% de escritura"])
    else:
        st.info("No hay datos disponibles")

    st.subheader("Conexiones (última hora)")
    df = get_throttled_requests_metrics(selected_table)
    if not df.empty:
        st.line_chart(df.set_index("instante")["Conexiones"])
    else:
        st.info("No hay datos disponibles")
