import traceback
from datetime import datetime, timezone
import io, base64
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:
    matplotlib = None
    plt = None
    MATPLOTLIB_AVAILABLE = False
from utils.tag_filter import get_tag_filter


SERVICE_DESCRIPTIONS = {
    "arquitectura": (
        "Vista consolidada de los recursos desplegados y sus conexiones. "
        "Útil para identificar dependencias y puntos de integración entre servicios."
    ),
    "ecs": (
        "Elastic Container Service gestiona los contenedores de la aplicación. "
        "Aquí se listan los clusters activos, sus servicios y las tareas en ejecución."
    ),
    "ecr": (
        "Elastic Container Registry almacena las imágenes Docker de la plataforma. "
        "Se muestra el número de repositorios, imágenes y si el escaneo de vulnerabilidades está activo."
    ),
    "rds": (
        "Relational Database Service proporciona las bases de datos relacionales gestionadas. "
        "Se incluye estado, configuración Multi-AZ y almacenamiento provisionado."
    ),
    "dynamodb": (
        "Base de datos NoSQL serverless de AWS. "
        "Se detallan las tablas activas, el número de elementos y las métricas de throughput."
    ),
    "s3": (
        "Simple Storage Service aloja objetos y archivos estáticos. "
        "Se listan los buckets con su región y métricas de tamaño y actividad."
    ),
    "cognito": (
        "Gestiona la autenticación y el registro de usuarios de la aplicación. "
        "Se muestran los user pools configurados y métricas de inicios de sesión y registros."
    ),
    "sns": (
        "Simple Notification Service distribuye mensajes a múltiples suscriptores. "
        "Se listan los topics activos, suscripciones y volumen de publicaciones."
    ),
    "sqs": (
        "Simple Queue Service desacopla componentes mediante colas de mensajes. "
        "Se incluyen mensajes visibles, en proceso y métricas de flujo por cola."
    ),
    "vpc": (
        "Virtual Private Cloud define la red privada de la infraestructura. "
        "Se detalla el estado de cada VPC y la configuración de resolución DNS."
    ),
    "security_groups": (
        "Los grupos de seguridad controlan el tráfico entrante y saliente de los recursos. "
        "Se incluye un mapa de conectividad por grupo para identificar la superficie de red expuesta."
    ),
    "iam": (
        "Identity and Access Management controla permisos y accesos a la cuenta AWS. "
        "Se listan usuarios, roles y el estado del MFA para detectar posibles riesgos de seguridad."
    ),
    "cloudformation": (
        "CloudFormation gestiona la infraestructura como código mediante stacks declarativos. "
        "Se muestra el estado de cada stack y los recursos que lo componen."
    ),
    "elasticache": (
        "ElastiCache provee cachés en memoria (Redis/Memcached) para reducir la latencia. "
        "Se detallan los clusters, grupos de replicación y métricas de CPU y memoria libre."
    ),
    "costs": (
        "Estimación del gasto del mes en curso por servicio AWS. "
        "Permite identificar los servicios con mayor impacto económico y detectar anomalías."
    ),
}


# Helpers
def _df_to_md(df) -> str:
    """Convierte un DataFrame a tabla Markdown. Devuelve aviso si está vacío."""
    if df is None or df.empty:
        return "_Sin datos disponibles._"
    try:
        return df.to_markdown(index=False)
    except Exception:
        return "_Error al formatear los datos._"


def _section(title: str, level: int = 2) -> str:
    return f"\n{'#' * level} {title}\n\n"


def _error_block(service: str, exc: Exception) -> str:
    return (
        f"\n> ⚠️ **Error al obtener datos de {service}.**\n"
        f"> `{type(exc).__name__}: {exc}`\n"
    )


def _filter_notice(tag_filter: dict | None, service_supports_filter: bool) -> str:
    if tag_filter is None:
        return ""
    if service_supports_filter:
        # return f"> 🏷️ Filtro aplicado: **{tag_filter['key']}** = `{tag_filter['value']}`\n"
        return ""
    return "> ⚠️ Este servicio no soporta filtrado por etiqueta. Se muestran todos los recursos.\n"


def _service_description(key: str) -> str:
    desc = SERVICE_DESCRIPTIONS.get(key, "")
    return f"\n_{desc}_\n\n" if desc else ""


def _fig_to_md_image(fig, alt: str = "Gráfico") -> str:
    """Convierte una figura matplotlib a imagen base64 embebida en Markdown."""
    if not MATPLOTLIB_AVAILABLE:
        return "_Gráfico no disponible: falta dependencia `matplotlib`._"
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    return f"![{alt}](data:image/png;base64,{b64})\n\n\n"


def _build_metric_chart(df, time_col: str, value_col: str, title: str, ylabel: str, color: str = "#4A90D9") -> str:
    """Genera un gráfico de línea para una métrica temporal."""
    if not MATPLOTLIB_AVAILABLE:
        return "_Gráfico no disponible: falta dependencia `matplotlib`._"
    if df is None or df.empty:
        return "_Sin datos de métrica disponibles._"
    if time_col not in df.columns or value_col not in df.columns:
        return "_Sin datos de métrica disponibles (columnas no encontradas)._"

    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df[time_col], df[value_col], color=color, linewidth=1.5)
    ax.fill_between(df[time_col], df[value_col], alpha=0.15, color=color)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Tiempo")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, linestyle="--", alpha=0.4)
    return _fig_to_md_image(fig, title)


def _pick_existing_col(df, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _build_sg_connectivity_chart(nodes_df, edges_df, selected_group_id: str) -> str:
    if not MATPLOTLIB_AVAILABLE:
        return "_Gráfico no disponible: falta dependencia `matplotlib`._"
    if nodes_df is None or edges_df is None or nodes_df.empty or edges_df.empty:
        return "_Sin datos para generar el mapa de conectividad._"

    from matplotlib.patches import FancyBboxPatch

    def _draw_node(ax, x, y, text, facecolor, edgecolor):
        width = max(1.9, min(4.0, 1.2 + len(text) * 0.08))
        height = 0.65
        patch = FancyBboxPatch(
            (x - width / 2, y - height / 2),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=1.5,
        )
        ax.add_patch(patch)
        ax.text(x, y, text, ha="center", va="center", fontsize=9, color="#111111")
        return width, height

    def _node_size(text):
        return max(1.9, min(4.0, 1.2 + len(text) * 0.08)), 0.65

    inbound_peers = nodes_df[(nodes_df["tipo"] == "peer") & (nodes_df["direccion"] == "Inbound")]
    outbound_peers = nodes_df[(nodes_df["tipo"] == "peer") & (nodes_df["direccion"] == "Outbound")]
    sg_node = nodes_df[nodes_df["tipo"] == "sg"]
    positions = {}
    size_map = {}

    def assign_positions(df, x, y_step=1.2):
        if df.empty:
            return
        offset = -((len(df) - 1) * y_step) / 2
        for idx, (_, row) in enumerate(df.iterrows()):
            positions[row["node_id"]] = (x, offset + idx * y_step)
            size_map[row["node_id"]] = _node_size(row["label"])

    max_nodes = max(len(inbound_peers), len(sg_node), len(outbound_peers), 1)
    y_step = 1.25 if max_nodes <= 6 else 1.45
    assign_positions(inbound_peers, x=-5.0, y_step=y_step)
    assign_positions(sg_node, x=0.0, y_step=y_step)
    assign_positions(outbound_peers, x=5.0, y_step=y_step)

    fig, ax = plt.subplots(figsize=(13, 6))
    y_extent = max(4.0, ((max_nodes - 1) * y_step) / 2 + 1.0)
    ax.set_xlim(-7.2, 7.2)
    ax.set_ylim(-y_extent, y_extent)
    ax.axis("off")
    ax.set_title(f"Mapa de {selected_group_id}", fontsize=12, loc="left")

    port_label_by_id = {row["node_id"]: row["label"] for _, row in nodes_df[nodes_df["tipo"] == "port"].iterrows()}
    incoming_by_port = {}
    outgoing_by_port = {}
    for _, edge in edges_df.iterrows():
        if str(edge["to_node"]).startswith("port:"):
            incoming_by_port.setdefault(edge["to_node"], []).append(edge)
        if str(edge["from_node"]).startswith("port:"):
            outgoing_by_port.setdefault(edge["from_node"], []).append(edge)

    aggregated_edges = {}
    for port_node_id, left_edges in incoming_by_port.items():
        right_edges = outgoing_by_port.get(port_node_id, [])
        for left in left_edges:
            for right in right_edges:
                if left.get("rule_id") != right.get("rule_id"):
                    continue
                key = (left["from_node"], right["to_node"], "Outbound" if str(port_node_id).startswith("port:Outbound:") else "Inbound")
                aggregated_edges.setdefault(key, {"labels": []})
                lbl = port_label_by_id.get(port_node_id, "")
                if lbl and lbl not in aggregated_edges[key]["labels"]:
                    aggregated_edges[key]["labels"].append(lbl)

    for (from_node, to_node, direction), data in aggregated_edges.items():
        if from_node not in positions or to_node not in positions:
            continue
        x1, y1 = positions[from_node]
        x2, y2 = positions[to_node]
        from_w, _ = size_map.get(from_node, (2.0, 0.65))
        to_w, _ = size_map.get(to_node, (2.0, 0.65))
        start_x = x1 + (from_w / 2) if x2 >= x1 else x1 - (from_w / 2)
        end_x = x2 - (to_w / 2) if x2 >= x1 else x2 + (to_w / 2)
        color = "#df7a00" if direction == "Outbound" else "#1f5e9c"
        ax.annotate("", xy=(end_x, y2), xytext=(start_x, y1), arrowprops={"arrowstyle": "->", "lw": 1.4, "color": color})
        label = ", ".join(data["labels"])
        if label:
            ax.text((start_x + end_x) / 2, (y1 + y2) / 2 + 0.12, label, ha="center", va="center", fontsize=8.5, color=color, bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.2})

    for _, node in nodes_df.iterrows():
        node_id = node["node_id"]
        if node_id not in positions:
            continue
        x, y = positions[node_id]
        if node["tipo"] == "sg":
            _draw_node(ax, x, y, node["label"], facecolor="#cfeecf", edgecolor="#2e8b57")
        elif node["tipo"] == "port":
            _draw_node(ax, x, y, node["label"], facecolor="#c9e4ff", edgecolor="#1f5e9c")
        else:
            _draw_node(ax, x, y, node["label"], facecolor="#f2f2f2", edgecolor="#696969")

    return _fig_to_md_image(fig, f"Mapa SG {selected_group_id}")


def _build_architecture_image(nodes: dict, edges: list[dict]) -> str:
    if not MATPLOTLIB_AVAILABLE:
        return "_Gráfico no disponible: falta dependencia `matplotlib`._"
    if not nodes:
        return "_No se detectaron recursos para construir el diagrama._"

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.axis("off")

    node_ids = list(nodes.keys())
    n = len(node_ids)
    if n == 0:
        return "_No se detectaron recursos para construir el diagrama._"

    order = ["waf", "cloudfront", "alb", "ecr", "ecs", "sns", "sqs", "rds", "dynamodb", "s3", "vpc"]
    layer_x = {k: i * 2.8 for i, k in enumerate(order)}
    grouped = {}
    for nid in node_ids:
        tipo = str(nodes[nid].get("tipo", "other"))
        grouped.setdefault(tipo, []).append(nid)
    x_positions = {}
    for tipo, ids in grouped.items():
        x = layer_x.get(tipo, len(order) * 2.8)
        count = len(ids)
        for idx, nid in enumerate(ids):
            y = ((count - 1) / 2 - idx) * 1.6
            x_positions[nid] = (x, y)
    if not x_positions:
        return "_No se detectaron recursos para construir el diagrama._"

    xs = [p[0] for p in x_positions.values()]
    ys = [p[1] for p in x_positions.values()]
    ax.set_xlim(min(xs) - 2.0, max(xs) + 2.0)
    ax.set_ylim(min(ys) - 2.5, max(ys) + 2.5)

    node_size = {}
    for nid in node_ids:
        x, y = x_positions[nid]
        label = str(nodes[nid].get("label", nid)).replace("\\n", " | ").replace("\n", " | ")
        width = max(1.8, min(3.8, 1.0 + len(label) * 0.07))
        node_size[nid] = (width, 0.6)
        ax.text(
            x, y, label,
            ha="center", va="center", fontsize=8,
            bbox={"boxstyle": "round,pad=0.35", "fc": "#eef5ff", "ec": "#4A90D9", "lw": 1.2},
        )

    for edge in edges:
        src = edge.get("source")
        dst = edge.get("target")
        if src not in x_positions or dst not in x_positions:
            continue
        x1, y1 = x_positions[src]
        x2, y2 = x_positions[dst]
        src_w, _ = node_size.get(src, (2.2, 0.6))
        dst_w, _ = node_size.get(dst, (2.2, 0.6))
        start_x = x1 + (src_w / 2) if x2 >= x1 else x1 - (src_w / 2)
        end_x = x2 - (dst_w / 2) if x2 >= x1 else x2 + (dst_w / 2)
        ax.annotate(
            "",
            xy=(end_x, y2),
            xytext=(start_x, y1),
            arrowprops={"arrowstyle": "->", "lw": 1.0, "color": "#6b7280"},
        )
        label = str(edge.get("label", "")).strip()
        if label:
            ax.text((start_x + end_x) / 2, (y1 + y2) / 2 + 0.12, label, fontsize=7, color="#374151")

    return _fig_to_md_image(fig, "Arquitectura y conexiones")


# Secciones del informe
def _build_header(tag_filter: dict | None) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Informe de infraestructura AWS",
        f"\n**Generado:** {now}  ",
    ]
    if tag_filter:
        lines.append(f"**Filtro activo:** `{tag_filter['key']}` = `{tag_filter['value']}`  ")
    else:
        lines.append("**Filtro activo:** Ninguno - se muestran todos los recursos  ")
    return "\n".join(lines)


def _build_toc(selected_sections: list[str]) -> str:
    lines = ["## Índice", ""]
    for key in selected_sections:
        if key not in SECTIONS:
            continue
        label = SECTIONS[key]["label"]
        lines.append(f"- [{label}](#sec-{key})")
    lines.append("")
    return "\n".join(lines)


# Secciones individuales
def _build_architecture_diagram(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("Arquitectura y conexiones"), _service_description("arquitectura")]
    try:
        from aws.arquitectura import get_architecture_graph
        nodes, edges = get_architecture_graph()
        lines.append(_build_architecture_image(nodes, edges))
    except Exception as exc:
        lines.append(_error_block("Arquitectura", exc))
    return "\n".join(lines)


def _build_ecs(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("ECS - Elastic Container Service"), _service_description("ecs")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.ecs import (
            get_clusters_dataframe,
            get_services_dataframe,
            get_cpu_metrics,
            get_memory_metrics,
        )

        clusters_df = get_clusters_dataframe()
        lines.append(_section("Clusters", 3))
        lines.append(_df_to_md(clusters_df))

        if not clusters_df.empty and "Cluster" in clusters_df.columns:
            for cluster in clusters_df["Cluster"].tolist():
                lines.append(_section(f"Servicios - {cluster}", 3))
                try:
                    services_df = get_services_dataframe(cluster)
                    lines.append(_df_to_md(services_df))

                    if include_charts and not services_df.empty and "Service" in services_df.columns:
                        for service in services_df["Service"].tolist():
                            lines.append(_section(f"Métricas - {service}", 4))
                            try:
                                cpu_df = get_cpu_metrics(cluster, service)
                                lines.append(_build_metric_chart(cpu_df, "instante", "cpu", f"CPU - {service}", "CPU (%)", "#4A90D9"))
                            except Exception as exc:
                                lines.append(_error_block(f"CPU metrics ({service})", exc))
                            try:
                                mem_df = get_memory_metrics(cluster, service)
                                lines.append(_build_metric_chart(mem_df, "instante", "memoria", f"Memoria - {service}", "Memoria (%)", "#E8784A"))
                            except Exception as exc:
                                lines.append(_error_block(f"Memory metrics ({service})", exc))
                except Exception as exc:
                    lines.append(_error_block(f"ECS servicios ({cluster})", exc))
    except Exception as exc:
        lines.append(_error_block("ECS", exc))
    return "\n".join(lines)


def _build_ecr(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("ECR - Elastic Container Registry"), _service_description("ecr")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.ecr import get_repositories_dataframe, describe_images
        import pandas as pd

        lines.append(_section("Repositorios", 3))
        repos_df = get_repositories_dataframe()
        lines.append(_df_to_md(repos_df))
        lines.append("")

        if include_charts and MATPLOTLIB_AVAILABLE and repos_df is not None and not repos_df.empty and "Repositorio" in repos_df.columns:
            rows = []
            for repo_name in repos_df["Repositorio"].dropna().tolist():
                try:
                    img_count = len(describe_images(repo_name))
                except Exception:
                    img_count = 0
                rows.append({"Repositorio": repo_name, "Imágenes": img_count})

            if rows:
                chart_df = pd.DataFrame(rows).sort_values("Imágenes", ascending=True)
                fig, ax = plt.subplots(figsize=(10, max(3, len(chart_df) * 0.5)))
                ax.barh(chart_df["Repositorio"], chart_df["Imágenes"], color="#4A90D9")
                ax.set_title("Imágenes por repositorio ECR")
                ax.set_xlabel("Número de imágenes")
                ax.grid(axis="x", linestyle="--", alpha=0.35)
                lines.append(_fig_to_md_image(fig, "Imágenes por repositorio ECR"))
    except Exception as exc:
        lines.append(_error_block("ECR", exc))
    return "\n".join(lines)


def _build_rds(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("RDS - Relational Database Service"), _service_description("rds")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.rds import (
            get_rds_instances_dataframe,
            get_rds_cpu_metrics,
            get_rds_free_storage_metrics,
            get_rds_connections_metrics,
            get_rds_read_iops_metrics,
            get_rds_write_iops_metrics,
        )
        rds_df = get_rds_instances_dataframe()
        lines.append(_df_to_md(rds_df))

        if include_charts and not rds_df.empty and "ID Base de Datos" in rds_df.columns:
            for db_id in rds_df["ID Base de Datos"].dropna().tolist():
                lines.append(_section(f"Métricas - {db_id}", 4))
                metrics = [
                    ("CPU",           get_rds_cpu_metrics,            "cpu",          "CPU (%)",  "#4A90D9"),
                    ("Espacio libre", get_rds_free_storage_metrics,    "espacio libre","Bytes",    "#2E8B57"),
                    ("Conexiones",    get_rds_connections_metrics,     "conexiones",   "Conexiones","#8A63D2"),
                    ("Read IOPS",     get_rds_read_iops_metrics,       "read_iops",    "IOPS",     "#E8784A"),
                    ("Write IOPS",    get_rds_write_iops_metrics,      "write_iops",   "IOPS",     "#D9534F"),
                ]
                for label, fn, value_col, ylabel, color in metrics:
                    try:
                        lines.append(_build_metric_chart(fn(db_id), "instante", value_col, f"{label} - {db_id}", ylabel, color))
                    except Exception as exc:
                        lines.append(_error_block(f"RDS {label} ({db_id})", exc))
    except Exception as exc:
        lines.append(_error_block("RDS", exc))
    return "\n".join(lines)


def _build_dynamodb(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("DynamoDB"), _service_description("dynamodb")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.dynamodb import (
            get_tables_dataframe,
            get_read_throughput_metrics,
            get_write_throughput_metrics,
            get_throttled_requests_metrics,
        )
        tables_df = get_tables_dataframe()
        lines.append(_df_to_md(tables_df))

        if include_charts and not tables_df.empty and "Nombre de Tabla" in tables_df.columns:
            for table_name in tables_df["Nombre de Tabla"].dropna().tolist():
                lines.append(_section(f"Métricas - {table_name}", 4))
                metrics = [
                    ("Lectura consumida",  get_read_throughput_metrics,    "% de Lectura",  "Unidades", "#4A90D9"),
                    ("Escritura consumida",get_write_throughput_metrics,   "% de escritura","Unidades", "#E8784A"),
                    ("Throttled requests", get_throttled_requests_metrics, "Conexiones",    "Eventos",  "#D9534F"),
                ]
                for label, fn, value_col, ylabel, color in metrics:
                    try:
                        lines.append(_build_metric_chart(fn(table_name), "instante", value_col, f"{label} - {table_name}", ylabel, color))
                    except Exception as exc:
                        lines.append(_error_block(f"DynamoDB {label} ({table_name})", exc))
    except Exception as exc:
        lines.append(_error_block("DynamoDB", exc))
    return "\n".join(lines)


def _build_s3(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("S3 - Simple Storage Service"), _service_description("s3")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.s3 import get_buckets_dataframe, get_bucket_size_metrics, get_request_metrics
        buckets_df = get_buckets_dataframe()
        lines.append(_df_to_md(buckets_df))

        if include_charts and not buckets_df.empty and "Bucket" in buckets_df.columns:
            for bucket_name in buckets_df["Bucket"].dropna().tolist():
                lines.append(_section(f"Métricas - {bucket_name}", 4))
                metrics = [
                    ("Tamaño del bucket", get_bucket_size_metrics, "tamaño_gb", "GB",      "#2E8B57"),
                    ("Número de objetos", get_request_metrics,      "objetos",   "Objetos", "#8A63D2"),
                ]
                for label, fn, value_col, ylabel, color in metrics:
                    try:
                        lines.append(_build_metric_chart(fn(bucket_name), "instante", value_col, f"{label} - {bucket_name}", ylabel, color))
                    except Exception as exc:
                        lines.append(_error_block(f"S3 {label} ({bucket_name})", exc))
    except Exception as exc:
        lines.append(_error_block("S3", exc))
    return "\n".join(lines)


def _build_cognito(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("Cognito"), _service_description("cognito")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.cognito import get_user_pools_dataframe, get_sign_in_metrics, get_sign_up_metrics
        pools_df = get_user_pools_dataframe()
        lines.append(_df_to_md(pools_df))

        if include_charts and not pools_df.empty and "ID" in pools_df.columns:
            for pool_id in pools_df["ID"].dropna().tolist():
                lines.append(_section(f"Métricas - {pool_id}", 4))
                metrics = [
                    ("Inicios de sesión", get_sign_in_metrics, "Inicios de Sesión", "Eventos", "#4A90D9"),
                    ("Registros",         get_sign_up_metrics, "Registros",         "Eventos", "#E8784A"),
                ]
                for label, fn, value_col, ylabel, color in metrics:
                    try:
                        lines.append(_build_metric_chart(fn(pool_id), "instante", value_col, f"{label} - {pool_id}", ylabel, color))
                    except Exception as exc:
                        lines.append(_error_block(f"Cognito {label} ({pool_id})", exc))
    except Exception as exc:
        lines.append(_error_block("Cognito", exc))
    return "\n".join(lines)


def _build_sns(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("SNS - Simple Notification Service"), _service_description("sns")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.sns import get_topics_dataframe, get_publish_metrics
        topics_df = get_topics_dataframe()
        lines.append(_df_to_md(topics_df))

        if include_charts and not topics_df.empty and "ARN del Tema" in topics_df.columns:
            for topic_arn in topics_df["ARN del Tema"].dropna().tolist():
                topic_name = str(topic_arn).split(":")[-1] if topic_arn else "topic"
                lines.append(_section(f"Métricas - {topic_name}", 4))
                try:
                    metric_df = get_publish_metrics(topic_arn)
                    value_col = "Publicaciones" if "Publicaciones" in metric_df.columns else "NumberOfMessagesPublished"
                    lines.append(_build_metric_chart(metric_df, "instante", value_col, f"Publicaciones - {topic_name}", "Publicaciones", "#4A90D9"))
                except Exception as exc:
                    lines.append(_error_block(f"SNS Publicaciones ({topic_arn})", exc))
    except Exception as exc:
        lines.append(_error_block("SNS", exc))
    return "\n".join(lines)


def _build_sqs(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("SQS - Simple Queue Service"), _service_description("sqs")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.sqs import (
            get_queues_dataframe,
            get_messages_sent_metrics,
            get_messages_received_metrics,
            get_messages_deleted_metrics,
        )
        queues_df = get_queues_dataframe()
        lines.append(_df_to_md(queues_df))

        if include_charts and not queues_df.empty and "Nombre" in queues_df.columns:
            for queue_name in queues_df["Nombre"].dropna().tolist():
                lines.append(_section(f"Métricas - {queue_name}", 4))
                metrics = [
                    ("Mensajes enviados",    get_messages_sent_metrics,    ["NumberOfMessagesSent",    "Mensajes Enviados"],    "Mensajes", "#4A90D9"),
                    ("Mensajes recibidos",   get_messages_received_metrics, ["NumberOfMessagesReceived","Mensajes Recibidos"],   "Mensajes", "#2E8B57"),
                    ("Mensajes eliminados",  get_messages_deleted_metrics,  ["NumberOfMessagesDeleted", "Mensajes Eliminados"],  "Mensajes", "#E8784A"),
                ]
                for label, fn, candidate_cols, ylabel, color in metrics:
                    try:
                        metric_df = fn(queue_name)
                        value_col = _pick_existing_col(metric_df, candidate_cols)
                        if not value_col:
                            lines.append("_Sin datos de métrica disponibles (columnas no encontradas)._\n")
                            continue
                        lines.append(_build_metric_chart(metric_df, "instante", value_col, f"{label} - {queue_name}", ylabel, color))
                        lines.append("")
                    except Exception as exc:
                        lines.append(_error_block(f"SQS {label} ({queue_name})", exc))
    except Exception as exc:
        lines.append(_error_block("SQS", exc))
    return "\n".join(lines)


def _build_vpc(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("VPC - Virtual Private Cloud"), _service_description("vpc")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.vpc import get_vpcs_dataframe
        lines.append(_df_to_md(get_vpcs_dataframe()))
    except Exception as exc:
        lines.append(_error_block("VPC", exc))
    return "\n".join(lines)


def _build_security_groups(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("Grupos de seguridad"), _service_description("security_groups")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.security_groups import get_security_groups_dataframe, get_security_group_connectivity_dataframe
        groups_df = get_security_groups_dataframe()
        lines.append(_df_to_md(groups_df))
        lines.append("")

        if include_charts and not groups_df.empty and "ID del grupo" in groups_df.columns:
            for group_id in groups_df["ID del grupo"].dropna().tolist():
                lines.append(_section(f"Grafo de reglas - {group_id}", 4))
                try:
                    nodes_df, edges_df = get_security_group_connectivity_dataframe(group_id)
                    lines.append(_build_sg_connectivity_chart(nodes_df, edges_df, group_id))
                    lines.append("")
                except Exception as exc:
                    lines.append(_error_block(f"Security Groups grafo ({group_id})", exc))
    except Exception as exc:
        lines.append(_error_block("Security Groups", exc))
    return "\n".join(lines)


def _build_cloudformation(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("CloudFormation"), _service_description("cloudformation")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=False))
    try:
        from aws.cloudformation import get_stacks_dataframe, get_stack_resources_dataframe
        stacks_df = get_stacks_dataframe()
        lines.append(_section("Stacks", 3))
        lines.append(_df_to_md(stacks_df))
        lines.append("")

        if not stacks_df.empty and "Nombre del despliegue" in stacks_df.columns:
            for stack_name in stacks_df["Nombre del despliegue"].dropna().tolist():
                lines.append(_section(f"Recursos - {stack_name}", 4))
                try:
                    lines.append(_df_to_md(get_stack_resources_dataframe(stack_name)))
                    lines.append("")
                except Exception as exc:
                    lines.append(_error_block(f"CloudFormation recursos ({stack_name})", exc))
    except Exception as exc:
        lines.append(_error_block("CloudFormation", exc))
    return "\n".join(lines)


def _build_elasticache(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("ElastiCache"), _service_description("elasticache")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.elasticache import (
            get_clusters_dataframe,
            get_replication_groups_dataframe,
            get_cpu_metrics,
            get_freeable_memory_metrics,
        )
        clusters_df = get_clusters_dataframe()
        groups_df = get_replication_groups_dataframe()

        lines.append(_section("Clusters", 3))
        lines.append(_df_to_md(clusters_df))
        lines.append("")
        lines.append(_section("Replication Groups", 3))
        lines.append(_df_to_md(groups_df))
        lines.append("")

        if include_charts and not clusters_df.empty and "Cluster" in clusters_df.columns:
            for cluster_id in clusters_df["Cluster"].dropna().tolist():
                lines.append(_section(f"Métricas - {cluster_id}", 4))
                try:
                    lines.append(_build_metric_chart(get_cpu_metrics(cluster_id), "instante", "cpu", f"CPU - {cluster_id}", "CPU (%)", "#4A90D9"))
                except Exception as exc:
                    lines.append(_error_block(f"ElastiCache CPU ({cluster_id})", exc))
                try:
                    lines.append(_build_metric_chart(get_freeable_memory_metrics(cluster_id), "instante", "memoria_libre", f"Memoria libre - {cluster_id}", "Memoria libre", "#2E8B57"))
                except Exception as exc:
                    lines.append(_error_block(f"ElastiCache memoria ({cluster_id})", exc))
                lines.append("")
    except Exception as exc:
        lines.append(_error_block("ElastiCache", exc))
    return "\n".join(lines)


def _build_iam(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("IAM - Identity and Access Management"), _service_description("iam")]
    lines.append("> ⚠️ IAM es un servicio global de cuenta. El filtro por etiqueta no aplica en esta sección.\n")
    try:
        from aws.iam import get_users_dataframe, get_roles_dataframe
        lines.append(_section("Usuarios", 3))
        lines.append(_df_to_md(get_users_dataframe()))
        lines.append(_section("Roles", 3))
        lines.append(_df_to_md(get_roles_dataframe()))
    except Exception as exc:
        lines.append(_error_block("IAM", exc))
    return "\n".join(lines)


def _build_costs(tag_filter, include_charts: bool = True) -> str:
    lines = [_section("Costes - mes en curso"), _service_description("costs")]
    lines.append(_filter_notice(tag_filter, service_supports_filter=True))
    try:
        from aws.costs import estimate_costs
        costs_df = estimate_costs()
        lines.append(_df_to_md(costs_df))

        if include_charts and MATPLOTLIB_AVAILABLE and not costs_df.empty and {"Servicio", "Coste mensual ($)"} <= set(costs_df.columns):
            chart_df = costs_df.sort_values("Coste mensual ($)", ascending=False).head(10).iloc[::-1]
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.barh(chart_df["Servicio"], chart_df["Coste mensual ($)"], color="#4A90D9")
            ax.set_title("Coste mensual por servicio")
            ax.set_xlabel("USD")
            ax.grid(axis="x", linestyle="--", alpha=0.35)
            lines.append(_fig_to_md_image(fig, "Coste mensual por servicio"))

        if not costs_df.empty and "Coste mensual ($)" in costs_df.columns:
            total = costs_df["Coste mensual ($)"].sum()
            lines.append(f"\n**Coste total del mes: ${round(total, 2)}**\n")
    except Exception as exc:
        lines.append(_error_block("Cost Explorer", exc))
    return "\n".join(lines)


# Mapa de secciones disponibles
SECTIONS = {
    "arquitectura":    {"label": "Arquitectura y conexiones", "fn": _build_architecture_diagram},
    "ecs":             {"label": "ECS",                       "fn": _build_ecs},
    "ecr":             {"label": "ECR",                       "fn": _build_ecr},
    "rds":             {"label": "RDS",                       "fn": _build_rds},
    "dynamodb":        {"label": "DynamoDB",                  "fn": _build_dynamodb},
    "s3":              {"label": "S3",                        "fn": _build_s3},
    "cognito":         {"label": "Cognito",                   "fn": _build_cognito},
    "sns":             {"label": "SNS",                       "fn": _build_sns},
    "sqs":             {"label": "SQS",                       "fn": _build_sqs},
    "vpc":             {"label": "VPC",                       "fn": _build_vpc},
    "security_groups": {"label": "Grupos de seguridad",       "fn": _build_security_groups},
    "iam":             {"label": "IAM",                       "fn": _build_iam},
    "cloudformation":  {"label": "CloudFormation",            "fn": _build_cloudformation},
    "elasticache":     {"label": "ElastiCache",               "fn": _build_elasticache},
    "costs":           {"label": "Costes",                    "fn": _build_costs},
}


# Función principal para construir el informe completo
def build_report(selected_sections: list[str], include_charts: bool = True) -> str:
    tag_filter = get_tag_filter()
    parts = [_build_header(tag_filter)]

    try:
        parts.append(_build_toc(selected_sections))
    except Exception:
        parts.append("## Índice\n\n_No disponible por error de formato._\n")

    errors = []

    for key in selected_sections:
        if key not in SECTIONS:
            continue
        section_meta = SECTIONS[key]
        try:
            result = section_meta["fn"](tag_filter, include_charts)
            body = result if result else f"\n## {section_meta['label']}\n_Sin contenido._\n"
            parts.append(f"\n###### sec-{key}\n\n" + body + "\n\n\n---\n\n\n")
        except Exception as exc:
            error_detail = traceback.format_exc()
            errors.append(f"**{key}**: {exc}")
            parts.append(
                _section(section_meta["label"])
                + _error_block(section_meta["label"], exc)
                + f"\n```\n{error_detail}\n```\n"
            )

    parts.append("\n---\n## _Informe generado por AWS Monitor_\n")

    if errors:
        parts.append("\n## Errores durante la generación\n")
        for e in errors:
            parts.append(f"- {e}\n")

    return "\n\n\n".join(parts)