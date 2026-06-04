from config import get_mock_mode
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
import pandas as pd


def get_account_summary():

    if get_mock_mode():
        from mocks.iam_mock import get_account_summary
        return get_account_summary()

    try:
        iam = get_session().client("iam")

        summary = iam.get_account_summary()["SummaryMap"]

        return {
            "Usuarios": summary.get("Users", 0),
            "Roles": summary.get("Roles", 0),
            "Políticas": summary.get("Policies", 0),
            "Usuarios con MFA": summary.get("UsersWithMFADevice", 0),
            "MFA root habilitado": summary.get("AccountMFAEnabled", 0)
        }

    except Exception as exc:
        show_aws_error(exc, "IAM", "obtener resumen")
        return {}


def get_users_dataframe():

    if get_mock_mode():
        from mocks.iam_mock import get_users_dataframe
        return get_users_dataframe()

    try:
        iam = get_session().client("iam")

        users = iam.list_users()["Users"]

        rows = []

        for user in users:

            mfa_devices = iam.list_mfa_devices(
                UserName=user["UserName"]
            )["MFADevices"]

            rows.append({
                "Usuario": user["UserName"],
                "Fecha creación": user["CreateDate"],
                "ARN": user["Arn"],
                "MFA habilitado": len(mfa_devices) > 0,
                "Último uso consola": user.get("PasswordLastUsed")
            })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "IAM", "obtener usuarios")
        return pd.DataFrame()


def get_roles_dataframe():

    if get_mock_mode():
        from mocks.iam_mock import get_roles_dataframe
        return get_roles_dataframe()

    try:
        iam = get_session().client("iam")

        roles = iam.list_roles()["Roles"]

        rows = []

        for role in roles:

            role_name = role["RoleName"]

            attached = iam.list_attached_role_policies(
                RoleName=role_name
            )["AttachedPolicies"]

            inline = iam.list_role_policies(
                RoleName=role_name
            )["PolicyNames"]

            last_used = role.get("RoleLastUsed", {}).get("LastUsedDate")

            rows.append({
                "Rol": role_name,
                "Fecha creación": role["CreateDate"],
                "ARN": role["Arn"],
                "Último uso": last_used,
                "Políticas adjuntas": len(attached),
                "Políticas inline": len(inline),
                "Duración sesión": role.get("MaxSessionDuration")
            })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "IAM", "obtener roles")
        return pd.DataFrame()


def get_policies_dataframe():

    if get_mock_mode():
        from mocks.iam_mock import get_policies_dataframe
        return get_policies_dataframe()

    try:
        iam = get_session().client("iam")

        paginator = iam.get_paginator("list_policies")

        rows = []

        for page in paginator.paginate(Scope="Local"):

            for policy in page["Policies"]:

                rows.append({
                    "Nombre": policy["PolicyName"],
                    "ARN": policy["Arn"],
                    "Fecha creación": policy["CreateDate"],
                    "Adjunta": policy["AttachmentCount"],
                    "Versión": policy["DefaultVersionId"]
                })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "IAM", "obtener políticas")
        return pd.DataFrame()