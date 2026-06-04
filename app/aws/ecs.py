from config import get_mock_mode
from datetime import datetime, timedelta
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter, apply_tag_filter_to_list

import pandas as pd


def get_ecs_client():
    """Devuelve un cliente ECS construido con la sesion AWS activa."""
    return get_session().client("ecs")


def get_cloudwatch_client():
    """Devuelve un cliente CloudWatch para consultar metricas de ECS."""
    return get_session().client("cloudwatch")


def get_clusters_dataframe(apply_tag_filter: bool = True):
    """Lista clusters ECS y los transforma en un DataFrame para la UI."""

    if get_mock_mode():
        from mocks.ecs_mock import get_clusters_dataframe
        return get_clusters_dataframe()

    try:
        ecs = get_ecs_client()
        tag_filter = get_tag_filter() if apply_tag_filter else None

        cluster_arns = ecs.list_clusters().get("clusterArns", [])

        if not cluster_arns:
            return pd.DataFrame()

        clusters = ecs.describe_clusters(
            clusters=cluster_arns,
            include=["TAGS"],  # necesario para que la API devuelva las tags
        )["clusters"]

        # normalizar tags de ECS: vienen como [{"key": ..., "value": ...}]
        for c in clusters:
            c["tags"] = [
                {"Key": t["key"], "Value": t["value"]}
                for t in c.get("tags", [])
            ]

        clusters = apply_tag_filter_to_list(clusters, tag_filter)

        rows = []

        for c in clusters:
            rows.append({
                "Cluster": c["clusterName"],
                "Estado": c["status"],
                "Tareas en ejecución": c["runningTasksCount"],
                "Tareas pendientes": c["pendingTasksCount"],
                "Servicios": c["activeServicesCount"],
                "Instancias de contenedores": c["registeredContainerInstancesCount"],
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "ECS", "obtener clusters")
        return pd.DataFrame()


def get_services_dataframe(cluster_name, apply_tag_filter: bool = True):
    """Obtiene los servicios de un cluster y devuelve sus datos tabulares."""

    if get_mock_mode():
        from mocks.ecs_mock import get_services_dataframe
        return get_services_dataframe(cluster_name)

    try:
        ecs = get_ecs_client()
        tag_filter = get_tag_filter() if apply_tag_filter else None

        service_arns = ecs.list_services(cluster=cluster_name).get("serviceArns", [])

        if not service_arns:
            return pd.DataFrame()

        services = ecs.describe_services(
            cluster=cluster_name,
            services=service_arns,
            include=["TAGS"],
        )["services"]

        # Tags de servicios ECS también vienen en minúsculas
        for s in services:
            s["tags"] = [
                {"Key": t["key"], "Value": t["value"]}
                for t in s.get("tags", [])
            ]

        services = apply_tag_filter_to_list(services, tag_filter)

        rows = []

        for s in services:
            rows.append({
                "Service": s["serviceName"],
                "Estado": s["status"],
                "Tipo de lanzamiento": s.get("launchType", "N/A"),
                "Tareas deseadas": s["desiredCount"],
                "Tareas en ejecución": s["runningCount"],
                "Tareas pendientes": s["pendingCount"],
                "Definición de Tarea": s["taskDefinition"].split("/")[-1],
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "ECS", f"obtener servicios del cluster {cluster_name}")
        return pd.DataFrame()


def get_tasks_dataframe(cluster_name, service_name):
    """Recupera tareas de un servicio ECS y devuelve sus campos principales."""

    if get_mock_mode():
        from mocks.ecs_mock import get_tasks_dataframe
        return get_tasks_dataframe(cluster_name, service_name)

    try:
        ecs = get_ecs_client()

        task_arns = ecs.list_tasks(
            cluster=cluster_name,
            serviceName=service_name,
        ).get("taskArns", [])

        if not task_arns:
            return pd.DataFrame()

        tasks = ecs.describe_tasks(
            cluster=cluster_name,
            tasks=task_arns,
        )["tasks"]

        rows = []

        for t in tasks:
            rows.append({
                "ARN de Tarea": t["taskArn"].split("/")[-1],
                "Estado": t["lastStatus"],
                "CPU": t.get("cpu"),
                "Memoria (MB)": t.get("memory"),  # corregido: era t.get("memoria")
                "Tipo de lanzamiento": t.get("launchType"),
                "Fecha de comienzo": t.get("startedAt"),
            })

        dataframe = pd.DataFrame(rows)

        if not dataframe.empty:
            dataframe["Fecha de comienzo"] = pd.to_datetime(
                dataframe["Fecha de comienzo"],
                utc=True,
                errors="coerce",
            ).dt.tz_localize(None)

        return dataframe
    except Exception as exc:
        show_aws_error(exc, "ECS", f"obtener tareas del servicio {service_name}")
        return pd.DataFrame()


def get_cpu_metrics(cluster_name, service_name):
    """Consulta CPUUtilization en CloudWatch para el servicio indicado."""

    if get_mock_mode():
        from mocks.ecs_mock import get_cpu_metrics
        return get_cpu_metrics(cluster_name, service_name)

    try:
        cloudwatch = get_cloudwatch_client()

        end = datetime.utcnow()
        start = end - timedelta(minutes=30)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/ECS",
            MetricName="CPUUtilization",
            Dimensions=[
                {"Name": "ClusterName", "Value": cluster_name},
                {"Name": "ServiceName", "Value": service_name},
            ],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )

        rows = []

        for p in response.get("Datapoints", []):
            rows.append({
                "instante": p["Timestamp"],
                "cpu": p["Average"],
            })

        df = pd.DataFrame(rows)

        if not df.empty:
            df = df.sort_values("instante")

        return df
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (ECS)", f"obtener CPU del servicio {service_name}")
        return pd.DataFrame()


def get_memory_metrics(cluster_name, service_name):
    """Consulta MemoryUtilization en CloudWatch para el servicio indicado."""

    if get_mock_mode():
        from mocks.ecs_mock import get_memory_metrics
        return get_memory_metrics(cluster_name, service_name)

    try:
        cloudwatch = get_cloudwatch_client()

        end = datetime.utcnow()
        start = end - timedelta(minutes=30)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/ECS",
            MetricName="MemoryUtilization",
            Dimensions=[
                {"Name": "ClusterName", "Value": cluster_name},
                {"Name": "ServiceName", "Value": service_name},
            ],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )

        rows = []

        for p in response.get("Datapoints", []):
            rows.append({
                "instante": p["Timestamp"],
                "memoria": p["Average"],
            })

        df = pd.DataFrame(rows)

        if not df.empty:
            df = df.sort_values("instante")

        return df
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (ECS)", f"obtener memoria del servicio {service_name}")
        return pd.DataFrame()
