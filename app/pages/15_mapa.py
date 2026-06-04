import os
import math
import streamlit as st
import pydeck as pdk
import pandas as pd

from aws.mapa import (
    get_ecs_tasks_for_map,
    get_cloudfront_edges_for_map,
    get_service_nodes_for_map,
    get_summary_by_region,
    get_summary_by_az,
)
from config import get_mock_mode


st.set_page_config(page_title="Mapa de infraestructura", page_icon="🌍", layout="wide")

st.title("Mapa de infraestructura AWS")
st.caption("Distribución geográfica de tareas ECS y edge locations de CloudFront.")


@st.cache_data(ttl=60)
def load_data():
    tasks = get_ecs_tasks_for_map()
    edges = get_cloudfront_edges_for_map()
    service_nodes = get_service_nodes_for_map()
    return tasks, edges, service_nodes

with st.spinner("Consultando regiones AWS..."):
    tasks, edges, service_nodes = load_data()

if not tasks:
    st.info("No se encontraron tareas ECS desplegadas en ninguna región.")
    st.stop()

df_tasks   = pd.DataFrame(tasks)
df_edges   = pd.DataFrame(edges) if edges else pd.DataFrame()
df_nodes   = pd.DataFrame(service_nodes) if service_nodes else pd.DataFrame()
summary    = get_summary_by_region(tasks)
df_summary = pd.DataFrame(summary)


total     = len(tasks)
running   = len(df_tasks[df_tasks["status"] == "RUNNING"])
stopped   = len(df_tasks[df_tasks["status"] == "STOPPED"])
n_regions = df_tasks["region"].nunique()
n_edges   = len(edges)
n_nodes   = len(service_nodes)

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Tareas ECS totales",   total)
col2.metric("🟢 En ejecución",           running)
col3.metric("🔴 Detenidas",           stopped)
col4.metric("Regiones activas",     n_regions)
col5.metric("☁️ Edge locations CF",  n_edges)
col6.metric("Servicios adicionales", n_nodes)

st.divider()


col_c1, col_c2, col_c3, col_c4 = st.columns([2, 1, 1, 1])

with col_c1:
    vista = st.radio(
        "Vista del mapa",
        ["Columnas 3D por región", "Tareas individuales"],
        horizontal=True,
    )
with col_c2:
    solo_running = st.toggle("Solo tareas en ejecución", value=False)
with col_c3:
    mostrar_edges = st.toggle("Mostrar edge locations de CloudFront", value=True)
with col_c4:
    mostrar_servicios = st.toggle("Mostrar más servicios AWS", value=True)

if solo_running:
    df_tasks   = df_tasks[df_tasks["status"] == "RUNNING"]
    summary    = get_summary_by_region(df_tasks.to_dict("records"))
    df_summary = pd.DataFrame(summary)


layers = []

MAX_HEIGHT = 800_000
max_total  = df_summary["total"].max() if not df_summary.empty else 1
df_summary["elevation"] = (df_summary["total"] / max_total) * MAX_HEIGHT

if vista == "Columnas 3D por región":
    df_summary = df_summary.copy()
    df_summary["tip"] = df_summary.apply(
        lambda r: (
            f"{r['region_label']}\n"
            f"Running: {r['running']}\n"
            f"Stopped: {r['stopped']}\n"
            f"Total tareas: {r['total']}"
        ),
        axis=1,
    )
    layers.append(pdk.Layer(
        "ColumnLayer",
        data=df_summary,
        get_position="[lon, lat]",
        get_elevation="elevation",
        elevation_scale=0.5,
        radius=150_000,
        get_fill_color=[99, 179, 237, 200],
        get_line_color=[255, 255, 255, 50],
        pickable=True,
        auto_highlight=True,
        extruded=True,
))
else:
    df_tasks = df_tasks.copy()
    df_tasks["color"] = df_tasks["status"].apply(
        lambda s: [34, 197, 94, 210] if s == "RUNNING" else [239, 68, 68, 210]
    )
    df_tasks["tip"] = df_tasks.apply(
        lambda r: (
            f"{r['service']}\n"
            f"Cluster: {r['cluster']}\n"
            f"AZ: {r['az']}\n"
            f"Estado: {r['status']}\n"
            f"CPU: {r['cpu']} · Memoria: {r['memory']} MB"
        ),
        axis=1,
    )
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=df_tasks,
        get_position="[lon, lat]",
        get_color="color",
        get_radius=80_000,
        pickable=True,
        auto_highlight=True,
    ))

# Capa de edge locations CloudFront
if mostrar_edges and not df_edges.empty:
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=df_edges,
        get_position="[lon, lat]",
        get_color=[251, 191, 36, 180],
        get_radius=40_000,
        pickable=False,
    ))

if mostrar_servicios and not df_nodes.empty:
    color_map = {
        "ecs": [59, 130, 246, 230],
        "rds": [147, 51, 234, 230],
        "dynamodb": [249, 115, 22, 230],
        "s3": [16, 185, 129, 230],
        "sqs": [234, 179, 8, 230],
        "sns": [236, 72, 153, 230],
        "cognito": [99, 102, 241, 230],
    }
    df_nodes = df_nodes.copy()
    # Evita solapes cuando varios servicios caen en la misma región
    region_counts = df_nodes.groupby("region")["service"].transform("count")
    region_index = df_nodes.groupby("region").cumcount()
    base_offset = 0.35  # reduce separación para mantener nodos más compactos
    df_nodes["plot_lat"] = df_nodes["lat"] + (
        (base_offset * (region_counts > 1))
        * (region_index.map(lambda i: math.sin((2 * math.pi * i) / 8)))
    )
    df_nodes["plot_lon"] = df_nodes["lon"] + (
        (base_offset * (region_counts > 1))
        * (region_index.map(lambda i: math.cos((2 * math.pi * i) / 8)))
    )
    df_nodes["color"] = df_nodes["color_key"].apply(lambda k: color_map.get(k, [156, 163, 175, 230]))
    df_nodes["radius"] = df_nodes["count"].apply(lambda c: 14_000 + min(c, 20) * 3_000)
    df_nodes["is_ecs"] = df_nodes["service"].eq("ECS Tasks")
    df_nodes["ecs_radius"] = df_nodes["count"].apply(lambda c: 70_000 + min(c, 40) * 6_000)
    df_nodes["tip"] = df_nodes.apply(
        lambda r: (
            f"{r['service']}\n"
            f"Región: {r['region_label']}\n"
            f"Recursos: {r['count']}"
        ),
        axis=1,
    )
    df_ecs_bg = df_nodes[df_nodes["is_ecs"]].copy()
    if not df_ecs_bg.empty:
        df_ecs_bg["ecs_bg_color"] = [[59, 130, 246, 105]] * len(df_ecs_bg)
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=df_ecs_bg,
            get_position="[lon, lat]",
            get_color="ecs_bg_color",
            get_radius="ecs_radius",
            pickable=True,
            auto_highlight=True,
        ))

    df_non_ecs = df_nodes[~df_nodes["is_ecs"]].copy()
    if not df_non_ecs.empty:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=df_non_ecs,
            get_position="[plot_lon, plot_lat]",
            get_color="color",
            get_radius="radius",
            pickable=True,
            auto_highlight=True,
        ))

view_state = pdk.ViewState(
    latitude=30,
    longitude=10,
    zoom=1.5,
    pitch=45,
    bearing=0,
)

st.pydeck_chart(
    pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip={
            "text": "{tip}",
            "style": {"backgroundColor": "#1e293b", "color": "white", "borderRadius": "6px"},
        },
        map_style="mapbox://styles/mapbox/dark-v10",
        api_keys={"mapbox": os.getenv("MAPBOX_TOKEN", "")},
    ),
    width="stretch",
)

legend_cols = st.columns([1, 1, 1, 4])
legend_cols[0].markdown("🔵 **Región ECS**")
legend_cols[1].markdown("🟢 **En ejecución**")
legend_cols[2].markdown("🔴 **Detenidas**")
if mostrar_edges:
    legend_cols[3].markdown("🟡 **Edge location de CloudFront**")
if mostrar_servicios:
    st.caption("Servicios extra: ECS, RDS, DynamoDB, S3, SQS, SNS y Cognito.")

if mostrar_edges and df_edges.empty:
    st.caption("CloudFront no devolvió datos (sin distribuciones o sin permisos `cloudfront:ListDistributions`).")


st.divider()

col_t1, col_t2 = st.columns(2)

with col_t1:
    st.subheader("Resumen por región")
    st.dataframe(
        df_summary[["region_label", "running", "stopped", "total"]]
        .rename(columns={
            "region_label": "Región",
            "running":      "🟢 En ejecución",
            "stopped":      "🔴 Detenidas",
            "total":        "Total",
        })
        .sort_values("Total", ascending=False)
        .reset_index(drop=True),
        width='stretch',
        hide_index=True,
    )

with col_t2:
    st.subheader("Resumen por zona de disponibilidad")
    az_source = tasks if not solo_running else df_tasks.to_dict("records")
    df_az = get_summary_by_az(az_source)
    st.dataframe(df_az, width='stretch', hide_index=True)

if mostrar_servicios and not df_nodes.empty:
    st.subheader("Servicios adicionales por región")
    st.dataframe(
        df_nodes[["service", "region_label", "count"]]
        .rename(columns={
            "service": "Servicio",
            "region_label": "Región",
            "count": "Recursos",
        })
        .sort_values("Recursos", ascending=False)
        .reset_index(drop=True),
        width="stretch",
        hide_index=True,
    )
