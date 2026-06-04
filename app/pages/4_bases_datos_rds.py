import streamlit as st


from aws.rds import (
    get_rds_instances_dataframe,
    get_rds_cpu_metrics,
    get_rds_free_storage_metrics,
    get_rds_connections_metrics,
    get_rds_read_iops_metrics,
    get_rds_write_iops_metrics,
    get_rds_events,
    get_rds_snapshots
)
from utils.tag_filter import get_tag_filter

st.set_page_config(
    page_title="RDS",
    layout="wide"
)

st.title("Relational Database Service (RDS)")

instances_df = get_rds_instances_dataframe()

if instances_df.empty:
    tag_filter = get_tag_filter()
    if tag_filter:
        all_instances_df = get_rds_instances_dataframe(apply_tag_filter=False)
        if all_instances_df.empty:
            st.info("No se encontraron instancias RDS para monitorizar.")
        else:
            st.info(
                f"No se encontraron instancias RDS con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
    else:
        st.info("No se encontraron instancias RDS para monitorizar.")
    st.stop()

st.subheader("Instancias de base de datos")
st.dataframe(instances_df)

if not instances_df.empty:

    selected_db = st.selectbox(
        "Selecciona una instancia",
        instances_df["ID Base de Datos"]
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "CPU",
        "Almacenamiento",
        "Conexiones",
        "Operaciones E/S por segundo"
    ])

    with tab1:
        df = get_rds_cpu_metrics(selected_db)
        st.subheader("Uso de CPU (%)")
        if not df.empty:
            st.line_chart(df.set_index("instante")["cpu"])
        else:
            st.info("No hay datos disponibles")

    with tab2:
        df = get_rds_free_storage_metrics(selected_db)
        st.subheader("Espacio libre (bytes)")
        if not df.empty:
            st.line_chart(df.set_index("instante")["espacio libre"])
        else:
            st.info("No hay datos disponibles")

    with tab3:
        df = get_rds_connections_metrics(selected_db)
        st.subheader("Conexiones")
        if not df.empty:
            st.line_chart(df.set_index("instante")["conexiones"])
        else:
            st.info("No hay datos disponibles")

    with tab4:
        col1, col2 = st.columns(2)

        with col1:
            df = get_rds_read_iops_metrics(selected_db)
            st.subheader("Lectura (Read IOPS)")
            if not df.empty:
                st.line_chart(df.set_index("instante")["read_iops"])

        with col2:
            df = get_rds_write_iops_metrics(selected_db)
            st.subheader("Escritura (Write IOPS)")
            if not df.empty:
                st.line_chart(df.set_index("instante")["write_iops"])

    st.subheader("Eventos recientes")
    st.dataframe(get_rds_events(selected_db))

    st.subheader("Puntos de restauración (Snapshots)")
    st.dataframe(get_rds_snapshots(selected_db))
