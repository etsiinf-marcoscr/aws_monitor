import pandas as pd

VPCS = [
    {
        "VPC ID": "vpc-12345",
        "CIDR": "10.0.0.0/16",
        "Estado": "available",
        "Nombres de host DNS": True,
        "Resolución de DNS": True
    },
    {
        "VPC ID": "vpc-67890",
        "CIDR": "172.16.0.0/16",
        "Estado": "available",
        "Nombres de host DNS": False,
        "Resolución de DNS": True
    },
    {
        "VPC ID": "vpc-abcde",
        "CIDR": "192.168.0.0/16",
        "Estado": "available",
        "Nombres de host DNS": True,
        "Resolución de DNS": False
    }
]


SUBNETS = [
    {"Subnet ID": "subnet-a", "CIDR": "10.0.1.0/24", "AZ": "eu-west-1a", "IP disponibles": 251},
    {"Subnet ID": "subnet-b", "CIDR": "10.0.2.0/24", "AZ": "eu-west-1b", "IP disponibles": 251}
]


ROUTE_TABLES = [
    {"Route Table ID": "rtb-main", "Número rutas": 2, "Main": True},
    {"Route Table ID": "rtb-private", "Número rutas": 3, "Main": False}
]

ROUTES_BY_TABLE = {
    "rtb-main": [
        {"Destino": "10.0.0.0/16", "Dirección": "Salida", "Target": "local",        "Estado": "active"},
        {"Destino": "0.0.0.0/0",   "Dirección": "Salida", "Target": "igw-001",      "Estado": "active"},
    ],
    "rtb-private": [
        {"Destino": "10.0.0.0/16", "Dirección": "Salida", "Target": "local",        "Estado": "active"},
        {"Destino": "0.0.0.0/0",   "Dirección": "Salida", "Target": "nat-001",      "Estado": "active"},
        {"Destino": "10.1.0.0/16", "Dirección": "Entrada", "Target": "pcx-aabbcc", "Estado": "active"},
    ],
}


SECURITY_GROUPS = [
    {"Security Group": "default", "SG ID": "sg-001", "Inbound rules": 1, "Outbound rules": 1},
    {"Security Group": "web-sg", "SG ID": "sg-002", "Inbound rules": 2, "Outbound rules": 1}
]


INTERNET_GATEWAYS = [
    {"Internet Gateway ID": "igw-001", "Adjunta": True}
]


NAT_GATEWAYS = [
    {"NAT Gateway ID": "nat-001", "Subnet": "subnet-a", "Estado": "available"}
]


LOAD_BALANCERS = [
    {
        "Nombre": "alb-public-web",
        "ARN": "arn:aws:elasticloadbalancing:eu-west-1:123456789012:loadbalancer/app/alb-public-web/50dc6c495c0c9188",
        "Tipo": "application",
        "Esquema": "internet-facing",
        "Estado": "active",
        "DNS": "alb-public-web-123456.eu-west-1.elb.amazonaws.com",
        "Zona(s)": 2,
    },
    {
        "Nombre": "nlb-internal-api",
        "ARN": "arn:aws:elasticloadbalancing:eu-west-1:123456789012:loadbalancer/net/nlb-internal-api/60dc6c495c0c9199",
        "Tipo": "network",
        "Esquema": "internal",
        "Estado": "active",
        "DNS": "nlb-internal-api-123456.eu-west-1.elb.amazonaws.com",
        "Zona(s)": 2,
    },
]


def get_vpcs_dataframe():
    return pd.DataFrame(VPCS)


def get_subnets_dataframe(vpc_id):
    return pd.DataFrame(SUBNETS)


def get_route_tables_dataframe(vpc_id):
    return pd.DataFrame(ROUTE_TABLES)

def get_routes_by_table_dataframe(route_table_id: str) -> pd.DataFrame:
    rows = ROUTES_BY_TABLE.get(route_table_id, [])
    return pd.DataFrame(rows)


def get_security_groups_dataframe(vpc_id):
    return pd.DataFrame(SECURITY_GROUPS)


def get_internet_gateways_dataframe(vpc_id):
    return pd.DataFrame(INTERNET_GATEWAYS)


def get_nat_gateways_dataframe(vpc_id):
    return pd.DataFrame(NAT_GATEWAYS)


def get_load_balancers_dataframe(vpc_id):
    return pd.DataFrame(LOAD_BALANCERS)
