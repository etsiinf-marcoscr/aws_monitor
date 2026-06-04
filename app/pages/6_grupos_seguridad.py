import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


from aws.security_groups import (
    get_security_groups_dataframe,
    get_security_group_rules_dataframe,
    get_security_group_connectivity_dataframe,
)
from utils.tag_filter import get_tag_filter

st.set_page_config(
    page_title="SGs",
    layout="wide"
)

st.title("Security Groups (SGs)")


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


def render_connectivity_graph(nodes_df, edges_df, selected_group_id):
    if nodes_df.empty or edges_df.empty:
        st.caption("Sin datos para generar el mapa de conectividad.")
        return

    inbound_peers = nodes_df[(nodes_df["tipo"] == "peer") & (nodes_df["direccion"] == "Inbound")]
    outbound_peers = nodes_df[(nodes_df["tipo"] == "peer") & (nodes_df["direccion"] == "Outbound")]
    sg_node = nodes_df[nodes_df["tipo"] == "sg"]

    positions = {}
    size_map = {}

    def assign_positions(df, x, y_start=0.0, y_step=1.2):
        if df.empty:
            return
        offset = -((len(df) - 1) * y_step) / 2
        for idx, (_, row) in enumerate(df.iterrows()):
            positions[row["node_id"]] = (x, y_start + offset + idx * y_step)
            size_map[row["node_id"]] = _node_size(row["label"])

    max_nodes_in_column = max(len(inbound_peers), len(sg_node), len(outbound_peers), 1)
    y_step = 1.25 if max_nodes_in_column <= 6 else 1.45

    assign_positions(inbound_peers, x=-5.0, y_step=y_step)
    assign_positions(sg_node, x=0.0, y_step=y_step)
    assign_positions(outbound_peers, x=5.0, y_step=y_step)

    fig, ax = plt.subplots(figsize=(13, 6))
    y_extent = max(4.0, ((max_nodes_in_column - 1) * y_step) / 2 + 1.0)
    ax.set_xlim(-7.2, 7.2)
    ax.set_ylim(-y_extent, y_extent)
    ax.axis("off")
    ax.set_title(f"Mapa de {selected_group_id}", fontsize=12, loc="left")

    port_label_by_id = {
        row["node_id"]: row["label"]
        for _, row in nodes_df[nodes_df["tipo"] == "port"].iterrows()
    }
    incoming_by_port = {}
    outgoing_by_port = {}
    for _, edge in edges_df.iterrows():
        from_node = edge["from_node"]
        to_node = edge["to_node"]
        if to_node.startswith("port:"):
            incoming_by_port.setdefault(to_node, []).append(edge)
        if from_node.startswith("port:"):
            outgoing_by_port.setdefault(from_node, []).append(edge)

    direct_edges = []
    for port_node_id, left_edges in incoming_by_port.items():
        right_edges = outgoing_by_port.get(port_node_id, [])
        for left_edge in left_edges:
            for right_edge in right_edges:
                if left_edge.get("rule_id") != right_edge.get("rule_id"):
                    continue
                direct_edges.append({
                    "from_node": left_edge["from_node"],
                    "to_node": right_edge["to_node"],
                    "label": port_label_by_id.get(port_node_id, ""),
                    "direccion": "Outbound" if str(port_node_id).startswith("port:Outbound:") else "Inbound",
                })

    aggregated_edges = {}
    for edge in direct_edges:
        edge_key = (edge["from_node"], edge["to_node"], edge["direccion"])
        if edge_key not in aggregated_edges:
            aggregated_edges[edge_key] = {
                "from_node": edge["from_node"],
                "to_node": edge["to_node"],
                "direccion": edge["direccion"],
                "labels": [],
            }
        label = edge.get("label", "")
        if label and label not in aggregated_edges[edge_key]["labels"]:
            aggregated_edges[edge_key]["labels"].append(label)

    for edge in aggregated_edges.values():
        from_node = edge["from_node"]
        to_node = edge["to_node"]
        if from_node not in positions or to_node not in positions:
            continue
        x1, y1 = positions[from_node]
        x2, y2 = positions[to_node]

        from_w, _ = size_map.get(from_node, (2.0, 0.65))
        to_w, _ = size_map.get(to_node, (2.0, 0.65))

        start_x = x1 + (from_w / 2) if x2 >= x1 else x1 - (from_w / 2)
        end_x = x2 - (to_w / 2) if x2 >= x1 else x2 + (to_w / 2)

        ax.annotate(
            "",
            xy=(end_x, y2),
            xytext=(start_x, y1),
            arrowprops={
                "arrowstyle": "->",
                "lw": 1.4,
                "color": "#df7a00" if edge.get("direccion") == "Outbound" else "#1f5e9c",
            },
        )
        mid_x = (start_x + end_x) / 2
        mid_y = (y1 + y2) / 2 + 0.12
        labels = edge.get("labels", [])
        label = ", ".join(labels)
        if label:
            ax.text(
                mid_x,
                mid_y,
                label,
                ha="center",
                va="center",
                fontsize=8.5,
                color="#df7a00" if edge.get("direccion") == "Outbound" else "#1f5e9c",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.2},
            )

    for _, node in nodes_df.iterrows():
        node_id = node["node_id"]
        if node_id not in positions:
            continue

        x, y = positions[node_id]
        if node["tipo"] == "sg":
            _draw_node(
                ax,
                x,
                y,
                node["label"],
                facecolor="#cfeecf",
                edgecolor="#2e8b57",
            )
        elif node["tipo"] == "port":
            _draw_node(ax, x, y, node["label"], facecolor="#c9e4ff", edgecolor="#1f5e9c")
        else:
            _draw_node(ax, x, y, node["label"], facecolor="#f2f2f2", edgecolor="#696969")

    st.pyplot(fig, clear_figure=True, width="stretch")
    st.caption(
        "Verde: grupo principal | Gris: origen/destino (IP/CIDR/SG) | Flecha azul: inbound | Flecha naranja: outbound | Etiqueta en flecha: protocolo/puerto(s)"
    )

groups = get_security_groups_dataframe()

if groups.empty:
    tag_filter = get_tag_filter()
    if tag_filter:
        all_groups = get_security_groups_dataframe(apply_tag_filter=False)
        if all_groups.empty:
            st.info("No se encontraron security groups para monitorizar.")
        else:
            st.info(
                f"No se encontraron security groups con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
    else:
        st.info("No se encontraron security groups para monitorizar.")
else:
    groups_table = groups.copy()
    groups_table["VPC asociada"] = groups_table["VPC asociada"].apply(
        lambda vpc_id: f"http://localhost:8501/?selected_vpc={vpc_id}" if vpc_id else None
    )

    st.dataframe(
        groups_table,
        width='stretch',
        hide_index=True,
        column_config={
            "VPC asociada": st.column_config.LinkColumn(
                "VPC asociada",
                help="Abre la pagina de VPC con esa VPC seleccionada",
                display_text=r"selected_vpc=([^&]+)",
            )
        },
    )

    selected = st.selectbox(
        "Seleccione un grupo de seguridad",
        groups["ID del grupo"]
    )

    st.write("Grupo elegido:", selected)

    rules_df = get_security_group_rules_dataframe(selected)
    if rules_df.empty:
        st.info("No se encontraron reglas para este security group")
    else:
        if "__is_egress" in rules_df.columns:
            inbound_rules = rules_df[~rules_df["__is_egress"]]
            outbound_rules = rules_df[rules_df["__is_egress"]]
        else:
            inbound_rules = rules_df[rules_df["Dirección"] == "Inbound"]
            outbound_rules = rules_df[rules_df["Dirección"] == "Outbound"]

        columns_to_hide = ["Dirección", "__is_egress"]
        inbound_display = inbound_rules.drop(columns=columns_to_hide, errors="ignore")
        outbound_display = outbound_rules.drop(columns=columns_to_hide, errors="ignore")

        st.subheader("Reglas de Entrada (Inbound)")
        if inbound_rules.empty:
            st.caption("Sin reglas inbound")
        else:
            st.dataframe(inbound_display, width='stretch')

        st.subheader("Reglas de Salida (Outbound)")
        if outbound_rules.empty:
            st.caption("Sin reglas outbound")
        else:
            st.dataframe(outbound_display, width='stretch')

        st.subheader("Mapa de conectividad SG")
        nodes_df, edges_df = get_security_group_connectivity_dataframe(selected)
        render_connectivity_graph(nodes_df, edges_df, selected)
