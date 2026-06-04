import pandas as pd

SECURITY_GROUP_GRAPH_NODE_COLUMNS = ["node_id", "label", "tipo", "direccion"]
SECURITY_GROUP_GRAPH_EDGE_COLUMNS = [
    "from_node",
    "to_node",
    "label",
    "direccion",
    "rule_id",
]


def get_security_groups_dataframe():

    rows = [
        {
            "ID del grupo": "sg-123456",
            "Nombre": "web-servers",
            "VPC asociada": "vpc-1a2b3c",
            "Descripción": "Allow HTTP and HTTPS"
        },
        {
            "ID del grupo": "sg-789012",
            "Nombre": "database",
            "VPC asociada": "vpc-4d5e6f",
            "Descripción": "Allow MySQL"
        }
    ]

    return pd.DataFrame(rows)


def get_security_group_rules_dataframe(group_id):

    mock_rules = {
        "sg-123456": [
            {
                "Rule ID": "sgr-in-001",
                "Dirección": "Inbound",
                "__is_egress": False,
                "Protocolo": "tcp",
                "Puertos": "80",
                "Origen / Destino": "0.0.0.0/0",
                "Descripción": "HTTP publico",
            },
            {
                "Rule ID": "sgr-in-002",
                "Dirección": "Inbound",
                "__is_egress": False,
                "Protocolo": "tcp",
                "Puertos": "443",
                "Origen / Destino": "0.0.0.0/0",
                "Descripción": "HTTPS publico",
            },
            {
                "Rule ID": "sgr-out-001",
                "Dirección": "Outbound",
                "__is_egress": True,
                "Protocolo": "all",
                "Puertos": "all",
                "Origen / Destino": "0.0.0.0/0",
                "Descripción": "Salida general",
            },
        ],
        "sg-789012": [
            {
                "Rule ID": "sgr-in-010",
                "Dirección": "Inbound",
                "__is_egress": False,
                "Protocolo": "tcp",
                "Puertos": "3306",
                "Origen / Destino": "SG:sg-123456",
                "Descripción": "MySQL desde web",
            },
            {
                "Rule ID": "sgr-out-010",
                "Dirección": "Outbound",
                "__is_egress": True,
                "Protocolo": "all",
                "Puertos": "all",
                "Origen / Destino": "0.0.0.0/0",
                "Descripción": "Salida general",
            },
        ],
    }

    return pd.DataFrame(mock_rules.get(group_id, []))


def get_security_group_connectivity_dataframe(group_id):
    rules_df = get_security_group_rules_dataframe(group_id)

    if rules_df.empty:
        return (
            pd.DataFrame(columns=SECURITY_GROUP_GRAPH_NODE_COLUMNS),
            pd.DataFrame(columns=SECURITY_GROUP_GRAPH_EDGE_COLUMNS),
        )

    nodes = {}
    edges = []

    sg_node_id = f"sg:{group_id}"
    nodes[sg_node_id] = {
        "node_id": sg_node_id,
        "label": group_id,
        "tipo": "sg",
        "direccion": "Both",
    }

    for _, row in rules_df.iterrows():
        direction = "Outbound" if bool(row.get("__is_egress")) else "Inbound"
        protocol = str(row.get("Protocolo", "-"))
        ports = str(row.get("Puertos", "-"))
        peer = str(row.get("Origen / Destino", "-"))
        rule_id = str(row.get("Rule ID", "-"))

        port_label = f"{protocol}:{ports}"
        port_node_id = f"port:{direction}:{port_label}"
        if port_node_id not in nodes:
            nodes[port_node_id] = {
                "node_id": port_node_id,
                "label": port_label,
                "tipo": "port",
                "direccion": direction,
            }

        peer_node_id = f"peer:{direction}:{peer}"
        if peer_node_id not in nodes:
            nodes[peer_node_id] = {
                "node_id": peer_node_id,
                "label": peer,
                "tipo": "peer",
                "direccion": direction,
            }

        if direction == "Inbound":
            edges.append({
                "from_node": peer_node_id,
                "to_node": port_node_id,
                "label": "allow",
                "direccion": direction,
                "rule_id": rule_id,
            })
            edges.append({
                "from_node": port_node_id,
                "to_node": sg_node_id,
                "label": "to SG",
                "direccion": direction,
                "rule_id": rule_id,
            })
        else:
            edges.append({
                "from_node": sg_node_id,
                "to_node": port_node_id,
                "label": "allow",
                "direccion": direction,
                "rule_id": rule_id,
            })
            edges.append({
                "from_node": port_node_id,
                "to_node": peer_node_id,
                "label": "to peer",
                "direccion": direction,
                "rule_id": rule_id,
            })

    return (
        pd.DataFrame(nodes.values(), columns=SECURITY_GROUP_GRAPH_NODE_COLUMNS),
        pd.DataFrame(edges, columns=SECURITY_GROUP_GRAPH_EDGE_COLUMNS),
    )
