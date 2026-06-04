from config import get_mock_mode
import pandas as pd
from datetime import datetime, timedelta
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter, apply_tag_filter_to_list


def get_dynamodb_client():
    """Devuelve un cliente DynamoDB."""
    return get_session().client("dynamodb")


def get_cloudwatch_client():
    """Devuelve un cliente CloudWatch para métricas de DynamoDB."""
    return get_session().client("cloudwatch")


def get_tables_dataframe(apply_tag_filter: bool = True):
    """Lista tablas DynamoDB y devuelve sus atributos clave en DataFrame."""

    if get_mock_mode():
        from mocks.dynamodb_mock import get_tables_dataframe
        return get_tables_dataframe()

    try:
        dynamodb = get_dynamodb_client()
        tag_filter = get_tag_filter() if apply_tag_filter else None

        table_names = dynamodb.list_tables().get("TableNames", [])
        rows = []

        for table_name in table_names:
            try:
                detail = dynamodb.describe_table(TableName=table_name).get("Table", {})
            except Exception:
                detail = {}

            if tag_filter:
                # El ARN viene en describe_table
                table_arn = detail.get("TableArn", "")
                try:
                    # DynamoDB devuelve tags como [{"Key": ..., "Value": ...}]
                    tags = dynamodb.list_tags_of_resource(
                        ResourceArn=table_arn
                    ).get("Tags", [])
                except Exception:
                    tags = []

                proxy = {"tags": tags}
                if not apply_tag_filter_to_list([proxy], tag_filter):
                    continue

            if detail:
                rows.append({
                    "Nombre de Tabla": table_name,
                    "Estado": detail.get("TableStatus"),
                    "Tamaño (Bytes)": detail.get("TableSizeBytes"),
                    "Elementos": detail.get("ItemCount"),
                    "% de Lectura": (
                        detail.get("BillingModeSummary", {}).get("BillingMode")
                        or detail.get("ProvisionedThroughput", {}).get("ReadCapacityUnits")
                    ),
                    "% de escritura": detail.get("ProvisionedThroughput", {}).get("WriteCapacityUnits"),
                    "Creada": detail.get("CreationDateTime"),
                })
            else:
                rows.append({
                    "Nombre de Tabla": table_name,
                    "Estado": "DESCONOCIDO",
                    "Tamaño (Bytes)": None,
                    "Elementos": None,
                    "% de Lectura": None,
                    "% de escritura": None,
                    "Creada": None,
                })

        dataframe = pd.DataFrame(rows)

        if not dataframe.empty:
            dataframe["Creada"] = pd.to_datetime(
                dataframe["Creada"],
                utc=True,
                errors="coerce",
            ).dt.tz_localize(None)

        return dataframe
    except Exception as exc:
        show_aws_error(exc, "DynamoDB", "obtener tablas")
        return pd.DataFrame()


def get_read_throughput_metrics(table_name):
    """Obtiene la métrica de capacidad de lectura consumida (última hora)."""

    if get_mock_mode():
        from mocks.dynamodb_mock import get_read_throughput_metrics
        return get_read_throughput_metrics(table_name)

    try:
        cloudwatch = get_cloudwatch_client()
        end = datetime.utcnow()
        start = end - timedelta(minutes=60)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/DynamoDB",
            MetricName="ConsumedReadCapacityUnits",
            Dimensions=[{"Name": "TableName", "Value": table_name}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Sum"],
        )

        datapoints = response.get("Datapoints", [])
        if not datapoints:
            return pd.DataFrame()

        return pd.DataFrame([
            {"instante": p["Timestamp"], "% de Lectura": p["Sum"]}
            for p in datapoints
        ]).sort_values("instante")
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (DynamoDB)", f"obtener lectura de {table_name}")
        return pd.DataFrame()


def get_write_throughput_metrics(table_name):
    """Obtiene la métrica de capacidad de escritura consumida (última hora)."""

    if get_mock_mode():
        from mocks.dynamodb_mock import get_write_throughput_metrics
        return get_write_throughput_metrics(table_name)

    try:
        cloudwatch = get_cloudwatch_client()
        end = datetime.utcnow()
        start = end - timedelta(minutes=60)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/DynamoDB",
            MetricName="ConsumedWriteCapacityUnits",
            Dimensions=[{"Name": "TableName", "Value": table_name}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Sum"],
        )

        datapoints = response.get("Datapoints", [])
        if not datapoints:
            return pd.DataFrame()

        return pd.DataFrame([
            {"instante": p["Timestamp"], "% de escritura": p["Sum"]}
            for p in datapoints
        ]).sort_values("instante")
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (DynamoDB)", f"obtener escritura de {table_name}")
        return pd.DataFrame()


def get_throttled_requests_metrics(table_name):
    """Obtiene conexiones en la última hora."""

    if get_mock_mode():
        from mocks.dynamodb_mock import get_throttled_requests_metrics
        return get_throttled_requests_metrics(table_name)

    try:
        cloudwatch = get_cloudwatch_client()
        end = datetime.utcnow()
        start = end - timedelta(minutes=60)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/DynamoDB",
            MetricName="UserErrors",
            Dimensions=[{"Name": "TableName", "Value": table_name}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Sum"],
        )

        datapoints = response.get("Datapoints", [])
        if not datapoints:
            return pd.DataFrame()

        return pd.DataFrame([
            {"instante": p["Timestamp"], "Conexiones": p["Sum"]}
            for p in datapoints
        ]).sort_values("instante")
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (DynamoDB)", f"obtener conexiones de {table_name}")
        return pd.DataFrame()
