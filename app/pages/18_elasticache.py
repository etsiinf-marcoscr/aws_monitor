import streamlit as st
from aws.elasticache import (
    get_clusters_dataframe,
    get_replication_groups_dataframe,
    get_cpu_metrics,
    get_freeable_memory_metrics,
)
from utils.tag_filter import get_tag_filter

st.set_page_config(
    page_title="ElastiCache",
    layout="wide"
)

st.title("ElastiCache")

st.header("Clusters")

clusters_df = get_clusters_dataframe()

if clusters_df.empty:
    tag_filter = get_tag_filter()

    if tag_filter:
        all_clusters_df = get_clusters_dataframe(apply_tag_filter=False)
        if all_clusters_df.empty:
            st.info("No se encontraron clusters de ElastiCache para monitorizar.")
        else:
            st.info(
                f"No se encontraron clusters de ElastiCache con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
    else:
        st.info("No se encontraron clusters de ElastiCache para monitorizar.")
    st.stop()

st.dataframe(clusters_df)

selected_cluster = st.selectbox(
    "Seleccionar cluster",
    clusters_df["Cluster"]
)

st.header("Grupos de replicación (Replication Groups)")

replication_groups_df = get_replication_groups_dataframe()

if replication_groups_df.empty:
    tag_filter = get_tag_filter()

    if tag_filter:
        all_groups_df = get_replication_groups_dataframe(apply_tag_filter=False)
        if all_groups_df.empty:
            st.info("No se encontraron grupos de replicación para monitorizar.")
        else:
            st.info(
                f"No se encontraron grupos de replicación con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
    else:
        st.info("No se encontraron grupos de replicación para monitorizar.")
else:
    st.dataframe(replication_groups_df)

st.header("Utilizacion de CPU")

cpu_df = get_cpu_metrics(selected_cluster)

if not cpu_df.empty:
    st.line_chart(cpu_df.set_index("instante")["cpu"])

st.header("Memoria libre")

memory_df = get_freeable_memory_metrics(selected_cluster)

if not memory_df.empty:
    memory_unit = memory_df["unidad_memoria"].mode().iloc[0]
    st.caption(f"Unidad mostrada: {memory_unit}")
    st.line_chart(memory_df.set_index("instante")["memoria_libre"])
