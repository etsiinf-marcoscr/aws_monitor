from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from aws.cloudformation import get_stacks_dataframe
from aws.cognito import get_user_pools_dataframe
from aws.costs import estimate_costs
from aws.dynamodb import get_tables_dataframe
from aws.ecr import get_repositories_dataframe
from aws.ecs import get_clusters_dataframe as get_ecs_clusters_dataframe
from aws.elasticache import (
    get_clusters_dataframe as get_elasticache_clusters_dataframe,
    get_replication_groups_dataframe,
)
from aws.iam import get_account_summary
from aws.rds import get_rds_instances_dataframe
from aws.s3 import get_buckets_dataframe
from aws.security_groups import get_security_groups_dataframe
from aws.sns import get_topics_dataframe
from aws.sqs import get_queues_dataframe
from aws.vpc import get_vpcs_dataframe
from config import get_mock_mode
from utils.tag_filter import get_tag_filter, is_filter_active


st.set_page_config(
    page_title="Panel de control",
    page_icon=":material/monitoring:",
    layout="wide",
)


SERVICE_COLORS = {
    "ECS": "#ff8a3d",
    "ECR": "#2f80ed",
    "ElastiCache": "#c2410c",
    "RDS": "#22a06b",
    "DynamoDB": "#7c3aed",
    "S3": "#16a34a",
    "VPC": "#0891b2",
    "Security Groups": "#475569",
    "IAM": "#be123c",
    "Cognito": "#9333ea",
    "SNS": "#ea580c",
    "SQS": "#ca8a04",
    "CloudFormation": "#2563eb",
    "Costes": "#0f766e",
}


def inject_dashboard_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.75rem;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem 1rem 0.85rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }

        div[data-testid="stMetric"] label {
            color: #64748b;
            font-size: 0.82rem;
        }

        div[data-testid="stMetricValue"] {
            color: #0f172a;
            font-size: 1.85rem;
        }

        .dashboard-hero {
            background: linear-gradient(135deg, #111827 0%, #1f2937 55%, #334155 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 1.35rem 1.45rem;
            color: white;
            margin-bottom: 1rem;
        }

        .dashboard-hero h1 {
            margin: 0;
            font-size: 2.05rem;
            letter-spacing: 0;
        }

        .dashboard-hero p {
            margin: 0.45rem 0 0;
            color: #cbd5e1;
            max-width: 860px;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.28rem 0.62rem;
            font-size: 0.78rem;
            font-weight: 700;
            background: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
        }

        .service-card {
            border: 1px solid #e5e7eb;
            border-left: 4px solid var(--accent);
            border-radius: 8px;
            padding: 0.9rem 1rem;
            background: #ffffff;
            min-height: 116px;
            margin-bottom: 0.75rem;
        }

        .service-card .label {
            color: #64748b;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            margin-bottom: 0.18rem;
            text-transform: uppercase;
        }

        .service-card .value {
            color: #0f172a;
            font-size: 1.28rem;
            font-weight: 750;
            line-height: 1.15;
            margin-bottom: 0.35rem;
        }

        .service-card .detail {
            color: #475569;
            font-size: 0.9rem;
            line-height: 1.36;
        }

        .compact-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=180) # 3 mins en caché
def load_dashboard_data(mock_mode: bool) -> dict[str, Any]:
    return {
        "ecs": get_ecs_clusters_dataframe(),
        "ecr": get_repositories_dataframe(),
        "rds": get_rds_instances_dataframe(),
        "s3": get_buckets_dataframe(),
        "dynamodb": get_tables_dataframe(),
        "vpcs": get_vpcs_dataframe(),
        "security_groups": get_security_groups_dataframe(),
        "iam": get_account_summary(),
        "cognito": get_user_pools_dataframe(),
        "sns": get_topics_dataframe(),
        "sqs": get_queues_dataframe(),
        "elasticache_clusters": get_elasticache_clusters_dataframe(),
        "elasticache_replication": get_replication_groups_dataframe(),
        "cloudformation": get_stacks_dataframe(),
        "costs": estimate_costs(),
    }


def count_rows(dataframe: pd.DataFrame | None) -> int:
    return 0 if dataframe is None or dataframe.empty else len(dataframe)


def find_column(dataframe: pd.DataFrame, candidates: list[str]) -> str | None:
    if dataframe.empty:
        return None

    normalized = {str(column).casefold(): column for column in dataframe.columns}
    for candidate in candidates:
        column = normalized.get(candidate.casefold())
        if column is not None:
            return column
    return None


def sum_column(dataframe: pd.DataFrame, candidates: list[str]) -> int:
    column = find_column(dataframe, candidates)
    if column is None:
        return 0
    return int(pd.to_numeric(dataframe[column], errors="coerce").fillna(0).sum())


def count_matching(dataframe: pd.DataFrame, candidates: list[str], value: Any) -> int:
    column = find_column(dataframe, candidates)
    if column is None:
        return 0
    return int((dataframe[column] == value).sum())


def count_contains(dataframe: pd.DataFrame, candidates: list[str], text: str) -> int:
    column = find_column(dataframe, candidates)
    if column is None:
        return 0
    return int(dataframe[column].astype(str).str.contains(text, case=False, na=False).sum())


def money(value: float) -> str:
    return f"${value:,.2f}"


def render_hero(total_resources: int) -> None:
    mode = "Simulación" if get_mock_mode() else "Cuenta AWS"
    filter_text = ""

    if is_filter_active() and not get_mock_mode():
        tag = get_tag_filter()
        filter_text = f" Filtro activo: {tag['key']} = {tag['value']}."

    st.markdown(
        f"""
        <div class="dashboard-hero">
            <span class="status-pill">Monitor activo</span>
            <h1>Panel de control AWS</h1>
            <p>
                Resumen de los servicios principales de la cuenta: cómputo, datos,
                red, identidad, mensajería, despliegues y costes. Origen: {mode}.
                Recursos visibles: {total_resources}.{filter_text}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_service_card(service: str, value: str, detail: str) -> None:
    color = SERVICE_COLORS.get(service, "#64748b")
    st.markdown(
        f"""
        <div class="service-card" style="--accent: {color};">
            <div class="label">{service}</div>
            <div class="value">{value}</div>
            <div class="detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_card_grid(cards: list[tuple[str, str, str]], columns: int = 3) -> None:
    for offset in range(0, len(cards), columns):
        cols = st.columns(columns)
        for col, card in zip(cols, cards[offset:offset + columns]):
            with col:
                render_service_card(*card)


def build_resource_mix(data: dict[str, Any], iam_summary: dict[str, Any]) -> pd.DataFrame:
    rows = [
        ("ECS", count_rows(data["ecs"])),
        ("ECR", count_rows(data["ecr"])),
        ("ElastiCache", count_rows(data["elasticache_clusters"])),
        ("RDS", count_rows(data["rds"])),
        ("DynamoDB", count_rows(data["dynamodb"])),
        ("S3", count_rows(data["s3"])),
        ("VPC", count_rows(data["vpcs"])),
        ("Security Groups", count_rows(data["security_groups"])),
        ("IAM", int(iam_summary.get("Usuarios", 0)) + int(iam_summary.get("Roles", 0))),
        ("Cognito", count_rows(data["cognito"])),
        ("SNS", count_rows(data["sns"])),
        ("SQS", count_rows(data["sqs"])),
        ("CloudFormation", count_rows(data["cloudformation"])),
    ]
    return pd.DataFrame(rows, columns=["Servicio", "Recursos"]).set_index("Servicio")


def render_cost_summary(costs_df: pd.DataFrame) -> tuple[float, str]:
    if costs_df.empty or "Coste mensual ($)" not in costs_df:
        return 0.0, "Sin datos"

    total = float(pd.to_numeric(costs_df["Coste mensual ($)"], errors="coerce").fillna(0).sum())
    top_service = str(costs_df.iloc[0].get("Servicio", "Sin datos"))
    return total, top_service


inject_dashboard_styles()

with st.spinner("Actualizando resumen de servicios AWS..."):
    data = load_dashboard_data(get_mock_mode())

iam_summary = data["iam"] or {}
cost_total, top_cost_service = render_cost_summary(data["costs"])
resource_mix_df = build_resource_mix(data, iam_summary)
total_resources = int(resource_mix_df["Recursos"].sum())

visible_sqs_messages = sum_column(data["sqs"], ["Mensajes Visibles Aprox."])
ecs_running_total = sum_column(data["ecs"], ["Tareas en ejecución", "Tareas en ejecucion"])
root_mfa_enabled = int(iam_summary.get("MFA root habilitado", 0)) == 1

render_hero(total_resources)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

with metric_1:
    st.metric("Recursos monitorizados", total_resources)
with metric_2:
    st.metric("Coste mes en curso", money(cost_total), delta=top_cost_service)
with metric_3:
    ecs_clusters_total = count_rows(data["ecs"])
    st.metric("Tareas ECS en ejecución", ecs_running_total, delta=f"{ecs_clusters_total} clusters")
with metric_4:
    st.metric("MFA root", "Activo" if root_mfa_enabled else "Revisar")

st.divider()

overview_left, overview_right = st.columns([1.1, 0.9])

with overview_left:
    st.subheader("Distribución por servicio")
    st.bar_chart(resource_mix_df, width="stretch")

with overview_right:
    st.subheader("Lecturas rápidas")
    ecr_scan = count_matching(data["ecr"], ["Escaneo al subir"], True)
    rds_multi_az = count_matching(data["rds"], ["Multi-AZ"], True)
    ddb_items = sum_column(data["dynamodb"], ["Elementos"])
    cf_failed = count_contains(data["cloudformation"], ["Estado"], "FAILED")

    render_service_card(
        "ECR",
        f"{ecr_scan} repos con escaneo",
        "Control básico para detectar vulnerabilidades en imágenes al subirlas.",
    )
    render_service_card(
        "RDS",
        f"{rds_multi_az} instancias Multi-AZ",
        "Alta disponibilidad de bases de datos relacionales.",
    )
    render_service_card(
        "DynamoDB",
        f"{ddb_items:,} elementos",
        "Volumen aproximado repartido entre las tablas monitorizadas.",
    )
    render_service_card(
        "CloudFormation",
        f"{cf_failed} stacks con fallo",
        "Estados FAILED detectados en despliegues declarativos.",
    )

st.divider()

tab_compute, tab_data, tab_network, tab_identity, tab_messaging, tab_delivery = st.tabs(
    ["Cómputo", "Datos", "Red", "Identidad", "Mensajería", "Coste y despliegue"]
)

with tab_compute:
    ecs_running = sum_column(data["ecs"], ["Tareas en ejecución", "Tareas en ejecucion"])
    ecs_services = sum_column(data["ecs"], ["Servicios"])
    ecs_pending = sum_column(data["ecs"], ["Tareas pendientes"])
    cache_nodes = sum_column(data["elasticache_clusters"], ["Nodos"])

    render_card_grid(
        [
            (
                "ECS",
                f"{count_rows(data['ecs'])} clusters",
                f"{ecs_services} servicios, {ecs_running} tareas en ejecución y {ecs_pending} pendientes.",
            ),
            (
                "ECR",
                f"{count_rows(data['ecr'])} repositorios",
                f"{ecr_scan} con escaneo al subir y "
                f"{count_matching(data['ecr'], ['Mutabilidad'], 'IMMUTABLE')} con tags inmutables.",
            ),
            (
                "ElastiCache",
                f"{count_rows(data['elasticache_clusters'])} clusters",
                f"{cache_nodes} nodos y {count_rows(data['elasticache_replication'])} grupos de replicación.",
            ),
        ]
    )

with tab_data:
    rds_available = count_matching(data["rds"], ["Estado"], "available")
    rds_storage = sum_column(data["rds"], ["Almacenamiento (GB)"])
    ddb_active = count_matching(data["dynamodb"], ["Estado"], "ACTIVE")
    s3_regions = find_column(data["s3"], ["Región", "Region"])
    unique_regions = data["s3"][s3_regions].nunique() if s3_regions else 0

    render_card_grid(
        [
            (
                "RDS",
                f"{rds_available}/{count_rows(data['rds'])} disponibles",
                f"{rds_multi_az} Multi-AZ y {rds_storage} GB provisionados.",
            ),
            (
                "DynamoDB",
                f"{ddb_active}/{count_rows(data['dynamodb'])} activas",
                f"{ddb_items:,} elementos y "
                f"{sum_column(data['dynamodb'], ['Tamaño (Bytes)', 'TamaÃ±o (Bytes)']) / 1024 / 1024:.1f} MB aprox.",
            ),
            (
                "S3",
                f"{count_rows(data['s3'])} buckets",
                f"Distribuidos en {unique_regions} regiones detectadas.",
            ),
        ]
    )

with tab_network:
    vpc_available = count_matching(data["vpcs"], ["Estado"], "available")
    dns_support = count_matching(data["vpcs"], ["Resolución de DNS", "ResoluciÃ³n de DNS"], True)

    render_card_grid(
        [
            (
                "VPC",
                f"{vpc_available}/{count_rows(data['vpcs'])} disponibles",
                f"{dns_support} con resolución DNS activa.",
            ),
            (
                "Security Groups",
                f"{count_rows(data['security_groups'])} grupos",
                "Resumen de superficie de reglas de red asociadas a EC2/VPC.",
            ),
        ],
        columns=2,
    )

with tab_identity:
    users = int(iam_summary.get("Usuarios", 0))
    roles = int(iam_summary.get("Roles", 0))
    users_with_mfa = int(iam_summary.get("Usuarios con MFA", 0))

    render_card_grid(
        [
            (
                "IAM",
                f"{users} usuarios / {roles} roles",
                f"{users_with_mfa} usuarios con MFA. MFA root: {'activo' if root_mfa_enabled else 'pendiente'}.",
            ),
            (
                "Cognito",
                f"{count_rows(data['cognito'])} user pools",
                "Entrada principal para autenticación de usuarios de aplicación.",
            ),
        ],
        columns=2,
    )

with tab_messaging:
    sqs_inflight = sum_column(data["sqs"], ["Mensajes No Visibles Aprox."])
    sns_subscriptions = sum_column(data["sns"], ["Suscripciones"])

    render_card_grid(
        [
            (
                "SQS",
                f"{count_rows(data['sqs'])} colas",
                f"{visible_sqs_messages} mensajes visibles y {sqs_inflight} en proceso.",
            ),
            (
                "SNS",
                f"{count_rows(data['sns'])} topics",
                f"{sns_subscriptions} suscripciones configuradas.",
            ),
        ],
        columns=2,
    )

with tab_delivery:
    cf_complete = count_contains(data["cloudformation"], ["Estado"], "COMPLETE")

    render_card_grid(
        [
            (
                "CloudFormation",
                f"{count_rows(data['cloudformation'])} stacks",
                f"{cf_complete} en estado COMPLETE y {cf_failed} con fallo.",
            ),
            (
                "Costes",
                money(cost_total),
                f"Servicio con más coste este mes: {top_cost_service}.",
            ),
        ],
        columns=2,
    )

    if not data["costs"].empty:
        st.markdown('<div class="compact-title">Top costes del mes</div>', unsafe_allow_html=True)
        st.dataframe(
            data["costs"].head(5).reset_index(drop=True),
            width="stretch",
            hide_index=True,
            column_config={
                "Coste mensual ($)": st.column_config.NumberColumn(format="$ %.2f"),
            },
        )
