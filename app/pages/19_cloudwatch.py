import streamlit as st
import pandas as pd
from aws.cloudwatch import (
    get_log_groups_dataframe,
    get_log_streams_dataframe,
    get_log_events_dataframe,
)
from datetime import datetime, timezone

st.set_page_config(page_title="Registros CloudWatch", layout="wide")
st.title("Registros (Logs) CloudWatch")

with st.expander("Filtros", expanded=True):
    col_prefix, col_ecs = st.columns([3, 1])
    with col_ecs:
        only_ecs = st.toggle("Solo grupos ECS", value=True)
    with col_prefix:
        default_prefix = "/ecs/" if only_ecs else ""
        prefix_input = st.text_input(
            "Prefijo del grupo de logs",
            value=default_prefix,
            placeholder="/ecs/  o  /aws/lambda/  …",
            disabled=only_ecs,
        )

prefix = "/ecs/" if only_ecs else prefix_input.strip()

st.subheader("Grupos de Logs")

log_groups_df = get_log_groups_dataframe(prefix_filter=prefix)

if log_groups_df.empty:
    st.info(f"No se encontraron grupos de logs con el prefijo `{prefix}`." if prefix else "No se encontraron grupos de logs.")
    st.stop()

st.dataframe(log_groups_df, hide_index=True, use_container_width=True)

selected_group = st.selectbox(
    "Selecciona un Grupo de Logs",
    log_groups_df["Grupo de Logs"],
    key="select_log_group",
)

st.subheader("Flujos (Streams) de Logs")
streams_df = get_log_streams_dataframe(selected_group)

if streams_df.empty:
    st.info("No se encontraron flujos de logs para este grupo.")
    st.stop()

st.dataframe(streams_df, hide_index=True, use_container_width=True)

selected_stream = st.selectbox(
    "Selecciona un Flujo de Logs",
    streams_df["Flujo de Logs"],
    key="select_log_stream",
)

with st.expander("Opciones de visualización", expanded=False):
    col_limit, col_level, col_search = st.columns(3)
    with col_limit:
        limit = st.slider("Máx. eventos a cargar", min_value=25, max_value=500, value=100, step=25)
    with col_level:
        level_filter = st.multiselect(
            "Filtrar por nivel",
            ["ERROR", "WARN", "INFO", "DEBUG"],
            default=[],
            placeholder="Todos los niveles",
        )
    with col_search:
        search_text = st.text_input("Buscar en mensaje", placeholder="NullPointerException …")

st.subheader("Eventos del Flujo")

events_df = get_log_events_dataframe(selected_group, selected_stream, limit=limit)

if events_df.empty:
    st.info("No se encontraron eventos en este stream.")
    st.stop()


def _detect_level(msg: str) -> str:
    m = msg.upper()
    for lvl in ("ERROR", "WARN", "WARNING", "CRITICAL", "DEBUG", "INFO"):
        if lvl in m:
            return "WARN" if lvl == "WARNING" else lvl
    return "INFO"


events_df["Nivel"] = events_df["Mensaje"].apply(_detect_level)
events_df["Fecha"] = events_df["Fecha"].apply(
    lambda ts: datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
)
events_df = events_df[["Fecha", "Nivel", "Mensaje"]]

# Aplicar filtros opcionales
if level_filter:
    events_df = events_df[events_df["Nivel"].isin(level_filter)]

if search_text:
    events_df = events_df[events_df["Mensaje"].str.contains(search_text, case=False, na=False)]

total  = len(events_df)
errors = len(events_df[events_df["Nivel"] == "ERROR"])
warns  = len(events_df[events_df["Nivel"] == "WARN"])

m1, m2, m3 = st.columns(3)
m1.metric("Total eventos",  total)
m2.metric("Errores",        errors, delta=f"-{errors}" if errors else None, delta_color="inverse")
m3.metric("Advertencias",   warns,  delta=f"-{warns}"  if warns  else None, delta_color="inverse")

LEVEL_COLOR = {
    "ERROR":    "#ff4b4b",
    "WARN":     "#ffa500",
    "INFO":     "#0e0d0d",
    "DEBUG":    "#888888",
    "CRITICAL": "#cc0000",
}

def _row_style(row):
    color = LEVEL_COLOR.get(row["Nivel"], "#e0e0e0")
    return [f"color: {color}"] * len(row)

styled = events_df.style.apply(_row_style, axis=1)

st.dataframe(
    styled,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Fecha": st.column_config.TextColumn("Fecha", width="small"),
        "Nivel":     st.column_config.TextColumn("Nivel",     width="small"),
        "Mensaje":   st.column_config.TextColumn("Mensaje",   width="large"),
    },
)