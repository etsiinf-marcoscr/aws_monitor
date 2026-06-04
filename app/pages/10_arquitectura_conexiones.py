import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
from aws.arquitectura import get_architecture_graph
from utils.tag_filter import is_filter_active
from config import get_mock_mode

st.set_page_config(page_title="Arquitectura y Conexiones", page_icon="🔗", layout="wide")

if is_filter_active() and not get_mock_mode():
    st.warning(
        "El filtro por etiqueta **no** ha sido implementado para esta sección, se mostrará una aproximación de la arquitectura completa inferida de los recursos desplegados.",
        icon="⚠️",
    )

st.title("Arquitectura y Conexiones")
st.caption("Grafo de interconexiones entre servicios AWS inferido de la configuración real mediante llamadas a la API de AWS. Algunos" \
" servicios pueden no mostrar las conexiones exactas por limitaciones de la API, pero se ha intentado reflejar lo más fielmente posible" \
" la arquitectura desplegada.")

# Colores por tipo de servicio 
TIPO_COLOR = {
    "cloudfront": "#F5A623",
    "s3":         "#3B87C8",
    "alb":        "#7B68EE",
    "waf":        "#E74C3C",
    "ecs":        "#FF6B35",
    "ecr":        "#2ECC71",
    "rds":        "#1ABC9C",
    "dynamodb":   "#9B59B6",
    "sns":        "#E67E22",
    "sqs":        "#F39C12",
    "vpc":        "#95A5A6",
}

TIPO_LABEL = {
    "cloudfront": "CloudFront",
    "s3":         "S3",
    "alb":        "ALB",
    "waf":        "WAF",
    "ecs":        "ECS",
    "ecr":        "ECR",
    "rds":        "RDS",
    "dynamodb":   "DynamoDB",
    "sns":        "SNS",
    "sqs":        "SQS",
    "vpc":        "VPC",
}


@st.cache_data(ttl=120)
def load_graph():
    return get_architecture_graph()

with st.spinner("Analizando conexiones entre servicios..."):
    nodes, edges = load_graph()

if not nodes:
    st.info("No se encontraron recursos desplegados para construir el grafo.")
    st.stop()


tipos_presentes = sorted({n["tipo"] for n in nodes.values()})
col_c1, col_c2 = st.columns([3, 1])

with col_c2:
    st.subheader("Filtrar por tipo")
    tipos_visibles = []
    for tipo in tipos_presentes:
        color = TIPO_COLOR.get(tipo, "#888")
        label = TIPO_LABEL.get(tipo, tipo.upper())
        checked = st.checkbox(f"{label}", value=True, key=f"chk_{tipo}")
        if checked:
            tipos_visibles.append(tipo)


def build_mermaid(nodes, edges, tipos_visibles):
    """Genera el string Mermaid a partir de nodos y aristas."""

    nodos_visibles = {
        nid: n for nid, n in nodes.items()
        if n["tipo"] in tipos_visibles
    }

    ids_visibles = set(nodos_visibles.keys())

    lines = ["graph LR"]

    style_lines = []
    for nid, node in nodos_visibles.items():
        color = TIPO_COLOR.get(node["tipo"], "#888")
        lines.append(f'    {nid}["{node["label"]}"]')
        style_lines.append(f"    style {nid} fill:{color},color:#fff,stroke:#333")

    lines.extend(style_lines)

    for edge in edges:
        if edge["source"] in ids_visibles and edge["target"] in ids_visibles:
            label = edge.get("label", "")
            if label:
                lines.append(f'    {edge["source"]} -->|{label}| {edge["target"]}')
            else:
                lines.append(f'    {edge["source"]} --> {edge["target"]}')

    return "\n".join(lines)

mermaid_str = build_mermaid(nodes, edges, tipos_visibles)


def render_mermaid(mermaid_code: str, height: int = 600):
    html = f"""
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad: true, theme: 'dark'}});</script>
    <div class="mermaid">
    {mermaid_code}
    </div>
    """
    encoded = urllib.parse.quote(html)
    st.iframe(f"data:text/html,{encoded}", height=height)

with col_c1:
    st.subheader("Grafo de arquitectura")
    render_mermaid(mermaid_str, height=650)

    with st.expander("Ver código Mermaid", expanded=False):
        st.code(mermaid_str, language="markdown")

# Exportar el diagrama como archivo Markdown con el bloque de código Mermaid
st.download_button(
    label="⬇️ Descargar diagrama Mermaid",
    data=f"```mermaid\n{mermaid_str}\n```",
    file_name="arquitectura_aws.md",
    mime="text/markdown",
)


st.divider()

col_l1, col_l2, col_l3 = st.columns(3)

with col_l1:
    st.subheader("Resumen")
    st.metric("Nodos totales", len(nodes))
    st.metric("Conexiones detectadas", len(edges))
    st.metric("Tipos de servicio", len(tipos_presentes))

with col_l2:
    st.subheader("Nodos por servicio")
    counts = {}
    for n in nodes.values():
        counts[TIPO_LABEL.get(n["tipo"], n["tipo"])] = counts.get(n["tipo"], 0) + 1
    for tipo, count in sorted(counts.items()):
        st.write(f"**{tipo}**: {count}")

with col_l3:
    st.subheader("Conexiones por tipo")
    edge_types = {}
    for e in edges:
        lbl = e.get("label", "sin etiqueta")
        edge_types[lbl] = edge_types.get(lbl, 0) + 1
    for lbl, count in sorted(edge_types.items(), key=lambda x: -x[1]):
        st.write(f"**{lbl}**: {count}")