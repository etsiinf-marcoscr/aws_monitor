"""
aws/mapa.py
Obtiene datos geográficos de ECS y CloudFront para el mapa de regiones.
Sigue el mismo patrón que el resto de módulos /aws del proyecto.
"""

import pandas as pd
from botocore.exceptions import ClientError

from config import get_mock_mode
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session

# Coordenadas fijas de regiones AWS - no vienen de la API, son constantes conocidas
from mocks.mapa_mock import REGION_COORDS


# Cliente
def get_ecs_client(region: str):
    if get_mock_mode():
        return None
    try:
        return get_session().client("ecs", region_name=region)
    except Exception as exc:
        show_aws_error(exc, "ECS", f"crear cliente en {region}")
        return None


def get_cloudfront_client():
    if get_mock_mode():
        return None
    try:
        # CloudFront es un servicio global, siempre usa us-east-1
        return get_session().client("cloudfront", region_name="us-east-1")
    except Exception as exc:
        show_aws_error(exc, "CloudFront", "crear cliente")
        return None


# ECS
# Regiones a consultar para ECS
ECS_REGIONS = list(REGION_COORDS.keys())

def _get_all_cluster_arns(ecs) -> list[str]:
    """Lista todos los ARNs de clusters en una región."""
    try:
        arns = []
        next_token = None
        while True:
            params = {}
            if next_token:
                params["nextToken"] = next_token
            response = ecs.list_clusters(**params)
            arns.extend(response.get("clusterArns", []))
            next_token = response.get("nextToken")
            if not next_token:
                break
        return arns
    except Exception:
        return []


def _get_tasks_for_cluster(ecs, cluster_arn: str) -> list[dict]:
    """Devuelve todas las tareas (RUNNING + STOPPED) de un cluster."""
    tasks = []
    for status in ["RUNNING", "STOPPED"]:
        try:
            next_token = None
            while True:
                params = {"cluster": cluster_arn, "desiredStatus": status}
                if next_token:
                    params["nextToken"] = next_token
                response = ecs.list_tasks(**params)
                task_arns = response.get("taskArns", [])
                if task_arns:
                    detail = ecs.describe_tasks(cluster=cluster_arn, tasks=task_arns)
                    tasks.extend(detail.get("tasks", []))
                next_token = response.get("nextToken")
                if not next_token:
                    break
        except Exception:
            continue
    return tasks


def get_ecs_tasks_for_map() -> list[dict]:
    """
    Recorre todas las regiones y devuelve las tareas ECS enriquecidas
    con coordenadas geográficas para el mapa.
    """
    if get_mock_mode():
        from mocks.mapa_mock import get_ecs_tasks_for_map
        raw = get_ecs_tasks_for_map()
        return _enrich_tasks_with_coords(raw)

    tasks = []
    for region in ECS_REGIONS:
        ecs = get_ecs_client(region)
        if ecs is None:
            continue
        try:
            cluster_arns = _get_all_cluster_arns(ecs)
            for cluster_arn in cluster_arns:
                cluster_name = cluster_arn.split("/")[-1]
                for task in _get_tasks_for_cluster(ecs, cluster_arn):
                    # Extraer nombre del servicio desde taskDefinitionArn
                    task_def = task.get("taskDefinitionArn", "")
                    service = task_def.split("/")[-1].rsplit(":", 1)[0] if task_def else "-"
                    az = task.get("availabilityZone", "-")
                    tasks.append({
                        "task_id":  task.get("taskArn", "").split("/")[-1],
                        "cluster":  cluster_name,
                        "service":  service,
                        "region":   region,
                        "az":       az,
                        "status":   task.get("lastStatus", "-"),
                        "cpu":      task.get("cpu", "-"),
                        "memory":   task.get("memory", "-"),
                    })
        except Exception as exc:
            show_aws_error(exc, "ECS", f"obtener tareas en {region}")
            continue

    return _enrich_tasks_with_coords(tasks)


def _enrich_tasks_with_coords(tasks: list[dict]) -> list[dict]:
    """Añade lat/lon y etiqueta de región a cada tarea."""
    enriched = []
    for task in tasks:
        coords = REGION_COORDS.get(task.get("region", ""))
        if not coords:
            continue
        enriched.append({
            **task,
            "lat":          coords["lat"],
            "lon":          coords["lon"],
            "region_label": coords["label"],
        })
    return enriched


# CloudFront - edge locations
def get_cloudfront_edges_for_map() -> list[dict]:
    """
    Devuelve las edge locations de CloudFront activas.
    En modo real usa la API de CloudFront para obtener las distribuciones
    y extrae sus orígenes; las edge locations son fijas y se toman del mock.
    """
    if get_mock_mode():
        from mocks.mapa_mock import get_cloudfront_edges_for_map
        return get_cloudfront_edges_for_map()

    # Las edge locations de CloudFront no se obtienen directamente por API
    try:
        cf = get_cloudfront_client()
        if cf is None:
            return []
        response = cf.list_distributions()
        items = response.get("DistributionList", {}).get("Items", [])
        if not items:
            return []
        # Si hay distribuciones activas, mostramos las edge locations conocidas
        from mocks.mapa_mock import get_cloudfront_edges_for_map
        return get_cloudfront_edges_for_map()
    except ClientError as exc:
        # Si faltan permisos de CloudFront, no interrumpimos el resto del mapa.
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"AccessDenied", "AccessDeniedException", "UnauthorizedOperation"}:
            return []
        show_aws_error(exc, "CloudFront", "obtener distribuciones para mapa")
        return []
    except Exception as exc:
        show_aws_error(exc, "CloudFront", "obtener distribuciones para mapa")
        return []


def _region_label(region: str) -> str:
    coords = REGION_COORDS.get(region, {})
    return coords.get("label", region)


def _append_node(nodes: list[dict], service: str, region: str, count: int, color: str):
    coords = REGION_COORDS.get(region)
    if not coords or count <= 0:
        return
    nodes.append({
        "service": service,
        "region": region,
        "region_label": _region_label(region),
        "count": count,
        "lat": coords["lat"],
        "lon": coords["lon"],
        "color_key": color,
    })


def get_service_nodes_for_map() -> list[dict]:
    """
    Devuelve nodos agregados por servicio/región para enriquecer el mapa
    (RDS, DynamoDB, SQS, SNS, Cognito y S3), además de ECS.
    """
    if get_mock_mode():
        from mocks.mapa_mock import get_service_nodes_for_map
        return get_service_nodes_for_map()

    nodes: list[dict] = []

    ecs_tasks = get_ecs_tasks_for_map()
    ecs_counts: dict[str, int] = {}
    for t in ecs_tasks:
        region = t.get("region")
        if not region:
            continue
        ecs_counts[region] = ecs_counts.get(region, 0) + 1
    for region, count in ecs_counts.items():
        _append_node(nodes, "ECS Tasks", region, count, "ecs")

    session = get_session()

    # RDS por región
    for region in ECS_REGIONS:
        try:
            rds = session.client("rds", region_name=region)
            instances = rds.describe_db_instances().get("DBInstances", [])
            _append_node(nodes, "RDS Instances", region, len(instances), "rds")
        except Exception:
            continue

    # DynamoDB por región
    for region in ECS_REGIONS:
        try:
            ddb = session.client("dynamodb", region_name=region)
            tables = ddb.list_tables().get("TableNames", [])
            _append_node(nodes, "DynamoDB Tables", region, len(tables), "dynamodb")
        except Exception:
            continue

    # SQS por región
    for region in ECS_REGIONS:
        try:
            sqs = session.client("sqs", region_name=region)
            queues = sqs.list_queues().get("QueueUrls", [])
            _append_node(nodes, "SQS Queues", region, len(queues), "sqs")
        except Exception:
            continue

    # SNS por región
    for region in ECS_REGIONS:
        try:
            sns = session.client("sns", region_name=region)
            topics = sns.list_topics().get("Topics", [])
            _append_node(nodes, "SNS Topics", region, len(topics), "sns")
        except Exception:
            continue

    # Cognito User Pools por región
    for region in ECS_REGIONS:
        try:
            cognito = session.client("cognito-idp", region_name=region)
            pools = cognito.list_user_pools(MaxResults=60).get("UserPools", [])
            _append_node(nodes, "Cognito Pools", region, len(pools), "cognito")
        except Exception:
            continue

    # S3 buckets por región
    try:
        s3 = session.client("s3")
        buckets = s3.list_buckets().get("Buckets", [])
        s3_counts: dict[str, int] = {}
        for b in buckets:
            try:
                loc = s3.get_bucket_location(Bucket=b["Name"])
                region = loc.get("LocationConstraint") or "us-east-1"
                s3_counts[region] = s3_counts.get(region, 0) + 1
            except Exception:
                continue
        for region, count in s3_counts.items():
            _append_node(nodes, "S3 Buckets", region, count, "s3")
    except Exception:
        pass

    return nodes


# Agregaciones para el mapa
def get_summary_by_region(tasks: list[dict]) -> list[dict]:
    """Agrupa tareas ECS por región con conteos de running/stopped."""
    summary: dict[str, dict] = {}
    for task in tasks:
        region = task["region"]
        if region not in summary:
            summary[region] = {
                "region":       region,
                "region_label": task["region_label"],
                "lat":          task["lat"],
                "lon":          task["lon"],
                "running":      0,
                "stopped":      0,
                "total":        0,
            }
        summary[region]["total"] += 1
        if task["status"] == "RUNNING":
            summary[region]["running"] += 1
        else:
            summary[region]["stopped"] += 1
    return list(summary.values())


def get_summary_by_az(tasks: list[dict]) -> pd.DataFrame:
    """Devuelve un DataFrame con el conteo de tareas por zona de disponibilidad."""
    if not tasks:
        return pd.DataFrame(columns=["AZ", "Región", "RUNNING", "STOPPED", "Total"])

    df = pd.DataFrame(tasks)
    grouped = (
        df.groupby(["az", "region_label"])
        .agg(
            RUNNING=("status", lambda x: (x == "RUNNING").sum()),
            STOPPED=("status", lambda x: (x == "STOPPED").sum()),
            Total=("task_id", "count"),
        )
        .reset_index()
        .rename(columns={"az": "AZ", "region_label": "Región"})
        .sort_values("Total", ascending=False)
    )
    return grouped
