import streamlit as st
from aws.ecs import (
    get_clusters_dataframe,
    get_services_dataframe,
    get_tasks_dataframe,
    get_cpu_metrics,
    get_memory_metrics
)
from utils.tag_filter import get_tag_filter

st.set_page_config(
    page_title="ECS",
    layout="wide"
)

st.title("Elastic Container Service (ECS)")

st.header("Clusters")

clusters_df = get_clusters_dataframe()

if clusters_df.empty:
    tag_filter = get_tag_filter()

    if tag_filter:
        all_clusters_df = get_clusters_dataframe(apply_tag_filter=False)
        if all_clusters_df.empty:
            st.info("No se encontraron clusters ECS para monitorizar.")
        else:
            st.info(
                f"No se encontraron clusters ECS con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
    else:
        st.info("No se encontraron clusters ECS para monitorizar.")
    st.stop()

st.dataframe(clusters_df)


selected_cluster = st.selectbox(
    "Seleccionar cluster",
    clusters_df["Cluster"]
)


st.header("Servicios")

services_df = get_services_dataframe(selected_cluster)

if services_df.empty:
    tag_filter = get_tag_filter()

    if tag_filter:
        all_services_df = get_services_dataframe(selected_cluster, apply_tag_filter=False)
        if all_services_df.empty:
            st.info("No se encontraron servicios para monitorizar en este cluster.")
        else:
            st.info(
                f"No se encontraron servicios con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}` en este cluster."
            )
    else:
        st.info("No se encontraron servicios para monitorizar en este cluster.")
    st.stop()

st.dataframe(services_df)


selected_service = st.selectbox(
    "Seleccionar servicio",
    services_df["Service"]
)


st.header("Tareas")

tasks_df = get_tasks_dataframe(
    selected_cluster,
    selected_service
)

if not tasks_df.empty:
    st.dataframe(tasks_df)


st.header("Utilización de CPU")

cpu_df = get_cpu_metrics(
    selected_cluster,
    selected_service
)

if not cpu_df.empty:
    st.line_chart(cpu_df.set_index("instante")["cpu"])


st.header("Utilización de Memoria")

memory_df = get_memory_metrics(
    selected_cluster,
    selected_service
)

if not memory_df.empty:
    st.line_chart(memory_df.set_index("instante")["memoria"])
