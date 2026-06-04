from config import get_mock_mode
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter
import pandas as pd


def get_vpcs_dataframe(apply_tag_filter: bool = True):
    """Lista VPCs y devuelve sus atributos clave en DataFrame."""

    if get_mock_mode():
        from mocks.vpc_mock import get_vpcs_dataframe
        return get_vpcs_dataframe()

    try:
        ec2 = get_session().client("ec2")
        tag_filter = get_tag_filter() if apply_tag_filter else None

        # EC2/VPC soporta filtrado nativo por tag en la API
        filters = []
        if tag_filter:
            filters.append({
                "Name": f"tag:{tag_filter['key']}",
                "Values": [tag_filter["value"]],
            })

        vpcs = ec2.describe_vpcs(Filters=filters)["Vpcs"]
        rows = []

        for vpc in vpcs:
            vpc_id = vpc["VpcId"]
            name = next(
                (t["Value"] for t in vpc.get("Tags", []) if t["Key"] == "Name"),
                "-",
            )
            dns_hostnames = ec2.describe_vpc_attribute(
                VpcId=vpc_id, Attribute="enableDnsHostnames"
            )["EnableDnsHostnames"]["Value"]

            dns_support = ec2.describe_vpc_attribute(
                VpcId=vpc_id, Attribute="enableDnsSupport"
            )["EnableDnsSupport"]["Value"]
            rows.append({
                "VPC ID": vpc["VpcId"],
                "Nombre": name,
                "CIDR": vpc["CidrBlock"],
                "Estado": vpc["State"],
                "Nombres de host DNS": dns_hostnames,
                "Resolución de DNS": dns_support,
            })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "VPC", "obtener VPCs")
        return pd.DataFrame()


def get_subnets_dataframe(vpc_id):
    """Lista subnets de una VPC en formato tabular."""

    if get_mock_mode():
        from mocks.vpc_mock import get_subnets_dataframe
        return get_subnets_dataframe(vpc_id)

    try:
        ec2 = get_session().client("ec2")

        subnets = ec2.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )["Subnets"]

        rows = []

        for s in subnets:
            rows.append({
                "Subnet ID": s["SubnetId"],
                "CIDR": s["CidrBlock"],
                "AZ": s["AvailabilityZone"],
                "IP disponibles": s["AvailableIpAddressCount"],
            })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "VPC", "obtener subnets")
        return pd.DataFrame()


def get_route_tables_dataframe(vpc_id):
    """Lista route tables de una VPC en formato tabular."""

    if get_mock_mode():
        from mocks.vpc_mock import get_route_tables_dataframe
        return get_route_tables_dataframe(vpc_id)

    try:
        ec2 = get_session().client("ec2")

        tables = ec2.describe_route_tables(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )["RouteTables"]

        rows = []

        for t in tables:
            rows.append({
                "Route Table ID": t["RouteTableId"],
                "Número rutas": len(t.get("Routes", [])),
                "Main": any(a.get("Main", False) for a in t["Associations"]),
            })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "VPC", "obtener route tables")
        return pd.DataFrame()
    
def get_routes_by_table_dataframe(route_table_id: str) -> pd.DataFrame:
    """
    Devuelve las rutas de entrada y salida de una tabla de ruta concreta.
    AWS no distingue 'entrada/salida' de forma nativa; las rutas en Routes[]
    son de salida. Las rutas de entrada (ingress) se corresponden con
    'GatewayRoutePropagations' o con el bloque 'Routes' de tipo 'propagated'.
    Aquí se etiquetan como 'Entrada' las rutas propagadas y 'Salida' el resto.
    """

    if get_mock_mode():
        from mocks.vpc_mock import get_routes_by_table_dataframe
        return get_routes_by_table_dataframe(route_table_id)

    try:
        ec2 = get_session().client("ec2")
        result = ec2.describe_route_tables(
            RouteTableIds=[route_table_id]
        )["RouteTables"]

        if not result:
            return pd.DataFrame()

        table = result[0]
        rows = []

        for r in table.get("Routes", []):
            destino = (
                r.get("DestinationCidrBlock")
                or r.get("DestinationIpv6CidrBlock")
                or r.get("DestinationPrefixListId")
                or "-"
            )
            target = (
                r.get("GatewayId")
                or r.get("NatGatewayId")
                or r.get("TransitGatewayId")
                or r.get("VpcPeeringConnectionId")
                or r.get("NetworkInterfaceId")
                or r.get("InstanceId")
                or "-"
            )
            # Las rutas propagadas se tratan como entrada
            direccion = "Entrada" if r.get("Origin") == "EnableVgwRoutePropagation" else "Salida"

            rows.append({
                "Destino": destino,
                "Dirección": direccion,
                "Target": target,
                "Estado": r.get("State", "-"),
            })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "VPC", "obtener rutas de la tabla")
        return pd.DataFrame()


def get_security_groups_dataframe(vpc_id):
    """Lista security groups de una VPC en formato tabular."""

    if get_mock_mode():
        from mocks.vpc_mock import get_security_groups_dataframe
        return get_security_groups_dataframe(vpc_id)

    try:
        ec2 = get_session().client("ec2")

        sgs = ec2.describe_security_groups(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )["SecurityGroups"]

        rows = []

        for sg in sgs:
            rows.append({
                "Security Group": sg["GroupName"],
                "SG ID": sg["GroupId"],
                "Inbound rules": len(sg["IpPermissions"]),
                "Outbound rules": len(sg["IpPermissionsEgress"]),
            })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "VPC", "obtener security groups")
        return pd.DataFrame()


def get_internet_gateways_dataframe(vpc_id):
    """Lista internet gateways adjuntos a una VPC."""

    if get_mock_mode():
        from mocks.vpc_mock import get_internet_gateways_dataframe
        return get_internet_gateways_dataframe(vpc_id)

    try:
        ec2 = get_session().client("ec2")

        igws = ec2.describe_internet_gateways(
            Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
        )["InternetGateways"]

        rows = []

        for igw in igws:
            rows.append({
                "Internet Gateway ID": igw["InternetGatewayId"],
                "Adjunta": len(igw["Attachments"]) > 0,
            })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "VPC", "obtener internet gateways")
        return pd.DataFrame()


def get_nat_gateways_dataframe(vpc_id):
    """Lista NAT gateways de una VPC en formato tabular."""

    if get_mock_mode():
        from mocks.vpc_mock import get_nat_gateways_dataframe
        return get_nat_gateways_dataframe(vpc_id)

    try:
        ec2 = get_session().client("ec2")

        nat = ec2.describe_nat_gateways(
            Filter=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )["NatGateways"]

        rows = []

        for g in nat:
            rows.append({
                "NAT Gateway ID": g["NatGatewayId"],
                "Subnet": g["SubnetId"],
                "Estado": g["State"],
            })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "VPC", "obtener NAT gateways")
        return pd.DataFrame()


def get_load_balancers_dataframe(vpc_id):
    """Lista load balancers (ALB/NLB/GWLB) asociados a una VPC."""

    if get_mock_mode():
        from mocks.vpc_mock import get_load_balancers_dataframe
        return get_load_balancers_dataframe(vpc_id)

    try:
        elbv2 = get_session().client("elbv2")
        rows = []
        marker = None

        while True:
            request = {}
            if marker:
                request["Marker"] = marker

            response = elbv2.describe_load_balancers(**request)
            for lb in response.get("LoadBalancers", []):
                if lb.get("VpcId") != vpc_id:
                    continue
                rows.append({
                    "Nombre": lb.get("LoadBalancerName"),
                    "ARN": lb.get("LoadBalancerArn"),
                    "Tipo": lb.get("Type"),
                    "Esquema": lb.get("Scheme"),
                    "Estado": lb.get("State", {}).get("Code"),
                    "DNS": lb.get("DNSName"),
                    "Zona(s)": len(lb.get("AvailabilityZones", [])),
                })

            marker = response.get("NextMarker")
            if not marker:
                break

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "ELBv2", "obtener load balancers de la VPC")
        return pd.DataFrame()
