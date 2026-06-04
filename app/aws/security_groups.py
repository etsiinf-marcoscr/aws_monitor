from config import get_mock_mode
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter
import pandas as pd


SECURITY_GROUP_COLUMNS = ["ID del grupo", "Nombre", "VPC asociada", "Descripción"]
SECURITY_GROUP_RULE_COLUMNS = [
    "Rule ID",
    "Dirección",
    "Protocolo",
    "Puertos",
    "Origen / Destino",
    "Descripción",
]
SECURITY_GROUP_RULE_INTERNAL_DIRECTION_COLUMN = "__is_egress"
SECURITY_GROUP_GRAPH_NODE_COLUMNS = ["node_id", "label", "tipo", "direccion"]
SECURITY_GROUP_GRAPH_EDGE_COLUMNS = [
    "from_node",
    "to_node",
    "label",
    "direccion",
    "rule_id",
]


def get_security_groups_dataframe(apply_tag_filter: bool = True):
    """Lista security groups EC2 y devuelve una vista tabular resumida."""

    if get_mock_mode():
        from mocks.security_groups_mock import get_security_groups_dataframe
        return get_security_groups_dataframe()

    try:
        ec2 = get_session().client("ec2")
        tag_filter = get_tag_filter() if apply_tag_filter else None

        # EC2 soporta filtrado nativo por tag en describe_security_groups
        filters = []
        if tag_filter:
            filters.append({
                "Name": f"tag:{tag_filter['key']}",
                "Values": [tag_filter["value"]],
            })

        groups = ec2.describe_security_groups(Filters=filters).get("SecurityGroups", [])

        rows = []

        for g in groups:
            rows.append({
                "ID del grupo": g["GroupId"],
                "Nombre": g["GroupName"],
                "VPC asociada": g.get("VpcId"),
                "Descripción": g["Description"],
            })

        return pd.DataFrame(rows, columns=SECURITY_GROUP_COLUMNS)
    except Exception as exc:
        show_aws_error(exc, "EC2/Security Groups", "obtener security groups")
        return pd.DataFrame(columns=SECURITY_GROUP_COLUMNS)


def _format_protocol(ip_protocol):
    if ip_protocol == "-1":
        return "all"
    return str(ip_protocol or "-")


def _format_ports(from_port, to_port, ip_protocol):
    if ip_protocol == "-1":
        return "all"
    if from_port is None and to_port is None:
        return "-"
    if from_port == to_port:
        return str(from_port)
    return f"{from_port}-{to_port}"


def _format_peer(rule):
    if rule.get("CidrIpv4"):
        return rule["CidrIpv4"]
    if rule.get("CidrIpv6"):
        return rule["CidrIpv6"]
    if rule.get("PrefixListId"):
        return f"PrefixList:{rule['PrefixListId']}"

    referenced_group = rule.get("ReferencedGroupInfo", {})
    if referenced_group.get("GroupId"):
        return f"SG:{referenced_group['GroupId']}"

    return "-"


def get_security_group_rules_dataframe(group_id):
    """Obtiene las reglas (inbound/outbound) de un security group."""

    if get_mock_mode():
        from mocks.security_groups_mock import get_security_group_rules_dataframe
        return get_security_group_rules_dataframe(group_id)

    try:
        ec2 = get_session().client("ec2")
        rules = []
        next_token = None

        while True:
            request = {
                "Filters": [{"Name": "group-id", "Values": [group_id]}],
            }
            if next_token:
                request["NextToken"] = next_token

            response = ec2.describe_security_group_rules(**request)
            rules.extend(response.get("SecurityGroupRules", []))
            next_token = response.get("NextToken")
            if not next_token:
                break

        rows = []

        for rule in rules:
            rows.append({
                "Rule ID": rule.get("SecurityGroupRuleId", "-"),
                "Dirección": "Outbound" if rule.get("IsEgress") else "Inbound",
                SECURITY_GROUP_RULE_INTERNAL_DIRECTION_COLUMN: bool(rule.get("IsEgress")),
                "Protocolo": _format_protocol(rule.get("IpProtocol")),
                "Puertos": _format_ports(
                    rule.get("FromPort"),
                    rule.get("ToPort"),
                    rule.get("IpProtocol"),
                ),
                "Origen / Destino": _format_peer(rule),
                "Descripción": rule.get("Description", ""),
            })

        columns = SECURITY_GROUP_RULE_COLUMNS + [SECURITY_GROUP_RULE_INTERNAL_DIRECTION_COLUMN]
        return pd.DataFrame(rows, columns=columns)
    except Exception as exc:
        show_aws_error(exc, "EC2/Security Groups", "obtener reglas de security group")
        columns = SECURITY_GROUP_RULE_COLUMNS + [SECURITY_GROUP_RULE_INTERNAL_DIRECTION_COLUMN]
        return pd.DataFrame(columns=columns)


def get_security_group_connectivity_dataframe(group_id):
    """Construye nodos y aristas para visualizar conectividad SG/puertos/peers."""

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
        direction = "Outbound" if bool(row.get(SECURITY_GROUP_RULE_INTERNAL_DIRECTION_COLUMN)) else "Inbound"
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
