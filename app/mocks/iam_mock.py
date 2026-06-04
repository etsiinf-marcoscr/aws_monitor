import pandas as pd
from datetime import datetime

USERS = [
    {
        "Usuario": "admin",
        "Fecha creación": datetime(2022, 5, 1),
        "ARN": "arn:aws:iam::123456789012:user/admin",
        "MFA habilitado": True,
        "Último uso consola": datetime(2025, 3, 10)
    },
    {
        "Usuario": "developer",
        "Fecha creación": datetime(2023, 2, 10),
        "ARN": "arn:aws:iam::123456789012:user/developer",
        "MFA habilitado": False,
        "Último uso consola": datetime(2025, 3, 8)
    },
    {
        "Usuario": "auditor",
        "Fecha creación": datetime(2024, 6, 20),
        "ARN": "arn:aws:iam::123456789012:user/auditor",
        "MFA habilitado": True,
        "Último uso consola": None
    }
]


ROLES = [
    {
        "Rol": "ecsTaskExecutionRole",
        "Fecha creación": datetime(2023, 5, 10),
        "ARN": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
        "Último uso": datetime(2025, 3, 10),
        "Políticas adjuntas": 2,
        "Políticas inline": 0,
        "Duración sesión": 3600
    },
    {
        "Rol": "rds-monitor-role",
        "Fecha creación": datetime(2024, 1, 2),
        "ARN": "arn:aws:iam::123456789012:role/rds-monitor-role",
        "Último uso": None,
        "Políticas adjuntas": 1,
        "Políticas inline": 1,
        "Duración sesión": 3600
    },
    {
        "Rol": "lambda-execution-role",
        "Fecha creación": datetime(2023, 9, 15),
        "ARN": "arn:aws:iam::123456789012:role/lambda-execution-role",
        "Último uso": datetime(2025, 2, 20),
        "Políticas adjuntas": 1,
        "Políticas inline": 0,
        "Duración sesión": 3600
    }
]


POLICIES = [
    {
        "Nombre": "AdminAccessCustom",
        "ARN": "arn:aws:iam::123456789012:policy/AdminAccessCustom",
        "Fecha creación": datetime(2023, 3, 10),
        "Adjunta": 2,
        "Versión": "v1"
    },
    {
        "Nombre": "ReadOnlyCustom",
        "ARN": "arn:aws:iam::123456789012:policy/ReadOnlyCustom",
        "Fecha creación": datetime(2024, 1, 15),
        "Adjunta": 1,
        "Versión": "v3"
    },
    {
        "Nombre": "S3BackupPolicy",
        "ARN": "arn:aws:iam::123456789012:policy/S3BackupPolicy",
        "Fecha creación": datetime(2023, 11, 2),
        "Adjunta": 2,
        "Versión": "v2"
    }
]


def get_account_summary():

    users_with_mfa = sum(u["MFA habilitado"] for u in USERS)

    return {
        "Usuarios": len(USERS),
        "Roles": len(ROLES),
        "Políticas": len(POLICIES),
        "Usuarios con MFA": users_with_mfa,
        "MFA root habilitado": 1
    }


def get_users_dataframe():
    return pd.DataFrame(USERS)


def get_roles_dataframe():
    return pd.DataFrame(ROLES)


def get_policies_dataframe():
    return pd.DataFrame(POLICIES)