from config import get_mock_mode
import pandas as pd
from datetime import datetime, timedelta
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter, apply_tag_filter_to_list


def get_rds_instances_dataframe(apply_tag_filter: bool = True):
    """Lista instancias RDS y devuelve sus atributos clave en DataFrame."""

    if get_mock_mode():
        from mocks.rds_mock import get_rds_instances_dataframe
        return get_rds_instances_dataframe()

    try:
        rds = get_session().client("rds")
        tag_filter = get_tag_filter() if apply_tag_filter else None

        response = rds.describe_db_instances()
        rows = []

        for db in response.get("DBInstances", []):

            if tag_filter:
                arn = db["DBInstanceArn"]
                tags_response = rds.list_tags_for_resource(ResourceName=arn)
                tags = {
                    t["Key"]: t["Value"]
                    for t in tags_response.get("TagList", [])
                }
                if tags.get(tag_filter["key"]) != tag_filter["value"]:
                    continue

            rows.append({
                "ID Base de Datos": db["DBInstanceIdentifier"],
                "Motor": db["Engine"],
                "Estado": db["DBInstanceStatus"],
                "Procesador": db["DBInstanceClass"],
                "Almacenamiento (GB)": db["AllocatedStorage"],
                "Multi-AZ": db["MultiAZ"],
                "Periodo de Backup": db["BackupRetentionPeriod"],
                "Endpoint": db.get("Endpoint", {}).get("Address"),
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "RDS", "obtener instancias")
        return pd.DataFrame()


def get_rds_cpu_metrics(db_identifier):
    """Obtiene la serie temporal de CPU de una instancia RDS."""

    if get_mock_mode():
        from mocks.rds_mock import get_rds_cpu_metrics
        return get_rds_cpu_metrics(db_identifier)

    try:
        cloudwatch = get_session().client("cloudwatch")

        end = datetime.utcnow()
        start = end - timedelta(minutes=30)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_identifier}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )

        return pd.DataFrame([
            {"instante": p["Timestamp"], "cpu": p["Average"]}
            for p in response.get("Datapoints", [])
        ]).sort_values("instante")
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (RDS)", f"obtener CPU de {db_identifier}")
        return pd.DataFrame()


def get_rds_free_storage_metrics(db_identifier):
    """Obtiene la metrica de espacio libre para una instancia RDS."""

    if get_mock_mode():
        from mocks.rds_mock import get_rds_free_storage_metrics
        return get_rds_free_storage_metrics(db_identifier)

    try:
        cloudwatch = get_session().client("cloudwatch")

        end = datetime.utcnow()
        start = end - timedelta(minutes=30)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName="FreeStorageSpace",
            Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_identifier}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )

        return pd.DataFrame([
            {"instante": p["Timestamp"], "espacio libre": p["Average"]}
            for p in response.get("Datapoints", [])
        ]).sort_values("instante")
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (RDS)", f"obtener espacio libre de {db_identifier}")
        return pd.DataFrame()


def get_rds_connections_metrics(db_identifier):
    """Obtiene el numero de conexiones activas de una instancia RDS."""

    if get_mock_mode():
        from mocks.rds_mock import get_rds_connections_metrics
        return get_rds_connections_metrics(db_identifier)

    try:
        cloudwatch = get_session().client("cloudwatch")

        end = datetime.utcnow()
        start = end - timedelta(minutes=30)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName="DatabaseConnections",
            Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_identifier}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )

        return pd.DataFrame([
            {"instante": p["Timestamp"], "conexiones": p["Average"]}
            for p in response.get("Datapoints", [])
        ]).sort_values("instante")
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (RDS)", f"obtener conexiones de {db_identifier}")
        return pd.DataFrame()


def get_rds_read_iops_metrics(db_identifier):
    """Obtiene el historico de ReadIOPS de una instancia RDS."""

    if get_mock_mode():
        from mocks.rds_mock import get_rds_read_iops_metrics
        return get_rds_read_iops_metrics(db_identifier)

    try:
        cloudwatch = get_session().client("cloudwatch")

        end = datetime.utcnow()
        start = end - timedelta(minutes=30)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName="ReadIOPS",
            Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_identifier}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )

        return pd.DataFrame([
            {"instante": p["Timestamp"], "read_iops": p["Average"]}
            for p in response.get("Datapoints", [])
        ]).sort_values("instante")
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (RDS)", f"obtener ReadIOPS de {db_identifier}")
        return pd.DataFrame()


def get_rds_write_iops_metrics(db_identifier):
    """Obtiene el historico de WriteIOPS de una instancia RDS."""

    if get_mock_mode():
        from mocks.rds_mock import get_rds_write_iops_metrics
        return get_rds_write_iops_metrics(db_identifier)

    try:
        cloudwatch = get_session().client("cloudwatch")

        end = datetime.utcnow()
        start = end - timedelta(minutes=30)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName="WriteIOPS",
            Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_identifier}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )

        return pd.DataFrame([
            {"instante": p["Timestamp"], "write_iops": p["Average"]}
            for p in response.get("Datapoints", [])
        ]).sort_values("instante")
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (RDS)", f"obtener WriteIOPS de {db_identifier}")
        return pd.DataFrame()


def get_rds_events(db_identifier):
    """Recupera eventos recientes de la instancia RDS (ultima hora)."""

    if get_mock_mode():
        from mocks.rds_mock import get_rds_events
        return get_rds_events(db_identifier)

    try:
        rds = get_session().client("rds")

        response = rds.describe_events(
            SourceIdentifier=db_identifier,
            SourceType="db-instance",
            Duration=60,
        )

        return pd.DataFrame(response.get("Events", []))
    except Exception as exc:
        show_aws_error(exc, "RDS", f"obtener eventos de {db_identifier}")
        return pd.DataFrame()


def get_rds_snapshots(db_identifier):
    """Lista snapshots de una instancia RDS en formato tabular."""

    if get_mock_mode():
        from mocks.rds_mock import get_rds_snapshots
        return get_rds_snapshots(db_identifier)

    try:
        rds = get_session().client("rds")

        response = rds.describe_db_snapshots(
            DBInstanceIdentifier=db_identifier
        )

        rows = []

        for s in response.get("DBSnapshots", []):
            rows.append({
                "Snapshot": s["DBSnapshotIdentifier"],
                "Estado": s["Status"],
                "Fecha de creación": s.get("SnapshotCreateTime"),
                "Tamaño (GB)": s.get("AllocatedStorage"),
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "RDS", f"obtener snapshots de {db_identifier}")
        return pd.DataFrame()
