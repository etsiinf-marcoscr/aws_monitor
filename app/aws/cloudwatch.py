from config import get_mock_mode
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
import pandas as pd
from datetime import datetime, timezone


def _ts_to_str(ts_ms: int) -> str:
    """Convierte timestamp en milisegundos a string legible UTC."""
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_log_groups_dataframe(prefix_filter: str = "") -> pd.DataFrame:
    """Lista log groups, opcionalmente filtrados por prefijo."""

    if get_mock_mode():
        from mocks.cloudwatch_mock import get_log_groups_dataframe
        return get_log_groups_dataframe(prefix_filter)

    try:
        logs = get_session().client("logs")
        rows = []
        kwargs = {}
        if prefix_filter:
            kwargs["logGroupNamePrefix"] = prefix_filter

        paginator = logs.get_paginator("describe_log_groups")
        for page in paginator.paginate(**kwargs):
            for lg in page.get("logGroups", []):
                retention = lg.get("retentionInDays")
                size_bytes = lg.get("storedBytes", 0)
                rows.append({
                    "Grupo de Logs":     lg["logGroupName"],
                    "Retención (días)": retention if retention else "Sin límite",
                    "Tamaño (MB)":      round(size_bytes / 1024 / 1024, 2),
                })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "CloudWatch Logs", "obtener log groups")
        return pd.DataFrame()


def get_log_streams_dataframe(log_group: str) -> pd.DataFrame:
    """Lista los streams de un log group, ordenados por evento más reciente."""

    if get_mock_mode():
        from mocks.cloudwatch_mock import get_log_streams_dataframe
        return get_log_streams_dataframe(log_group)

    try:
        logs = get_session().client("logs")
        rows = []

        paginator = logs.get_paginator("describe_log_streams")
        for page in paginator.paginate(
            logGroupName=log_group,
            orderBy="LastEventTime",
            descending=True,
        ):
            for s in page.get("logStreams", []):
                last_ts = s.get("lastEventTimestamp")
                rows.append({
                    "Flujo de Logs":   s["logStreamName"],
                    "Último evento": _ts_to_str(last_ts) if last_ts else "-",
                })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "CloudWatch Logs", "obtener log streams")
        return pd.DataFrame()


def get_log_events_dataframe(log_group: str, log_stream: str, limit: int = 200) -> pd.DataFrame:
    """
    Obtiene los últimos 'limit' eventos de un stream.
    Detecta el nivel (ERROR/WARN/INFO/DEBUG) para facilitar el filtrado en UI.
    """

    if get_mock_mode():
        from mocks.cloudwatch_mock import get_log_events_dataframe
        return get_log_events_dataframe(log_group, log_stream, limit)

    try:
        logs = get_session().client("logs")

        response = logs.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            limit=limit,
            startFromHead=False,
        )

        rows = []
        for e in response.get("events", []):
            rows.append({
                "Fecha": e["timestamp"],
                "Mensaje":   e["message"].rstrip("\n"),
            })

        return pd.DataFrame(rows)

    except Exception as exc:
        show_aws_error(exc, "CloudWatch Logs", "obtener eventos del stream")
        return pd.DataFrame()