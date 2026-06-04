from config import get_mock_mode
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter, apply_tag_filter_to_list
import pandas as pd


def get_cognito_client():
    """Devuelve un cliente Cognito Identity Provider."""
    return get_session().client("cognito-idp")


def get_cloudwatch_client():
    """Devuelve un cliente CloudWatch para consultar métricas de Cognito."""
    return get_session().client("cloudwatch")


def get_user_pools_dataframe(apply_tag_filter: bool = True):
    """Lista los User Pools y los transforma en un DataFrame para la UI."""

    if get_mock_mode():
        from mocks.cognito_mock import get_user_pools_dataframe
        return get_user_pools_dataframe()

    try:
        client = get_cognito_client()
        tag_filter = get_tag_filter() if apply_tag_filter else None

        response = client.list_user_pools(MaxResults=60)
        pools = response.get("UserPools", [])

        if tag_filter:
            # list_user_pools no soporta filtrado nativo por tag
            for pool in pools:
                try:
                    pool_arn = client.describe_user_pool(
                        UserPoolId=pool["Id"]
                    )["UserPool"]["UserPoolArn"]
                    raw_tags = client.list_tags_for_resource(
                        ResourceArn=pool_arn
                    ).get("Tags", {})
                    # Cognito devuelve tags como dict {"key": "value"}
                    pool["tags"] = [
                        {"Key": k, "Value": v} for k, v in raw_tags.items()
                    ]
                except Exception:
                    pool["tags"] = []

            pools = apply_tag_filter_to_list(pools, tag_filter)

        rows = []

        for p in pools:
            pool_id = p.get("Id")
            name = p.get("Name")

            try:
                detail = client.describe_user_pool(UserPoolId=pool_id).get("UserPool", {})
                created = detail.get("CreationDate")
            except Exception:
                created = None

            rows.append({
                "Grupo de Usuarios": name,
                "ID": pool_id,
                "Creado": created,
            })

        dataframe = pd.DataFrame(rows)

        if not dataframe.empty:
            dataframe["Creado"] = pd.to_datetime(
                dataframe["Creado"],
                utc=True,
                errors="coerce",
            ).dt.tz_localize(None)

        return dataframe
    except Exception as exc:
        show_aws_error(exc, "Cognito", "obtener user pools")
        return pd.DataFrame()


def get_user_pool_clients_dataframe(pool_id):
    """Lista los clientes (apps) de un User Pool."""

    if get_mock_mode():
        from mocks.cognito_mock import get_user_pool_clients_dataframe
        return get_user_pool_clients_dataframe(pool_id)

    try:
        client = get_cognito_client()

        response = client.list_user_pool_clients(UserPoolId=pool_id, MaxResults=60)
        clients = response.get("UserPoolClients", [])

        rows = []

        for c in clients:
            rows.append({
                "Nombre del Cliente": c.get("ClientName"),
                "ID del Cliente": c.get("ClientId"),
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "Cognito", f"obtener clientes del pool {pool_id}")
        return pd.DataFrame()


def get_users_dataframe(pool_id):
    """Lista usuarios de un User Pool y devuelve DataFrame con información relevante."""

    if get_mock_mode():
        from mocks.cognito_mock import get_users_dataframe
        return get_users_dataframe(pool_id)

    try:
        client = get_cognito_client()

        response = client.list_users(UserPoolId=pool_id)
        users = response.get("Users", [])

        rows = []

        for u in users:
            attrs = {a["Name"]: a["Value"] for a in u.get("Attributes", [])}
            rows.append({
                "Nombre de Usuario": u.get("Username"),
                "Estado": u.get("UserStatus"),
                "Habilitado": u.get("Enabled"),
                "Fecha creación": u.get("UserCreateDate"),
                "Última modificación": u.get("UserLastModifiedDate"),
                "Correo Electrónico": attrs.get("email"),
            })

        dataframe = pd.DataFrame(rows)

        if not dataframe.empty:
            for column in ("Fecha creación", "Última modificación"):
                dataframe[column] = pd.to_datetime(
                    dataframe[column],
                    utc=True,
                    errors="coerce",
                ).dt.tz_localize(None)

        return dataframe
    except Exception as exc:
        show_aws_error(exc, "Cognito", f"obtener usuarios del pool {pool_id}")
        return pd.DataFrame()


def get_user_counts(pool_id):
    """Devuelve estadísticas básicas del User Pool: totales y estados."""

    if get_mock_mode():
        from mocks.cognito_mock import get_user_counts
        return get_user_counts(pool_id)

    try:
        client = get_cognito_client()

        paginator = client.get_paginator("list_users")

        total = 0
        confirmed = 0
        unconfirmed = 0
        enabled = 0

        for page in paginator.paginate(UserPoolId=pool_id):
            for u in page.get("Users", []):
                total += 1
                if u.get("UserStatus") == "CONFIRMED":
                    confirmed += 1
                else:
                    unconfirmed += 1
                if u.get("Enabled"):
                    enabled += 1

        return {
            "total": total,
            "confirmed": confirmed,
            "unconfirmed": unconfirmed,
            "enabled": enabled,
            "disabled": total - enabled,
        }
    except Exception as exc:
        show_aws_error(exc, "Cognito", f"obtener estadísticas del pool {pool_id}")
        return {}


def _get_metric_dataframe(metric_name, dimension_name, dimension_value):
    """Helper para consultar CloudWatch y devolver un DataFrame con los datapoints."""

    try:
        cloudwatch = get_cloudwatch_client()

        from datetime import datetime, timedelta

        end = datetime.utcnow()
        start = end - timedelta(minutes=60)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/Cognito",
            MetricName=metric_name,
            Dimensions=[{"Name": dimension_name, "Value": dimension_value}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Sum"],
        )

        rows = []

        for p in response.get("Datapoints", []):
            rows.append({
                "instante": p["Timestamp"],
                metric_name: p.get("Sum"),
            })

        df = pd.DataFrame(rows)

        if not df.empty:
            df = df.sort_values("instante")

        return df
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (Cognito)", f"obtener métricas {metric_name} para {dimension_value}")
        return pd.DataFrame()


def get_sign_in_metrics(pool_id):
    """Consulta SignInSuccesses en CloudWatch para el User Pool indicado."""

    if get_mock_mode():
        from mocks.cognito_mock import get_sign_in_metrics
        return get_sign_in_metrics(pool_id)

    for dim in ("UserPoolId", "UserPool"):
        df = _get_metric_dataframe("SignInSuccesses", dim, pool_id)
        if not df.empty:
            return df.rename(columns={"SignInSuccesses": "Inicios de Sesión"})

    return pd.DataFrame()


def get_sign_up_metrics(pool_id):
    """Consulta SignUpSuccesses en CloudWatch para el User Pool indicado."""

    if get_mock_mode():
        from mocks.cognito_mock import get_sign_up_metrics
        return get_sign_up_metrics(pool_id)

    for dim in ("UserPoolId", "UserPool"):
        df = _get_metric_dataframe("SignUpSuccesses", dim, pool_id)
        if not df.empty:
            return df.rename(columns={"SignUpSuccesses": "Registros"})

    return pd.DataFrame()
