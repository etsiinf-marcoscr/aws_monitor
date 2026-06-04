from config import get_mock_mode
from datetime import datetime, timedelta
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter, apply_tag_filter_to_list

import pandas as pd


def get_elasticache_client():
    """Devuelve un cliente ElastiCache construido con la sesion AWS activa."""
    return get_session().client("elasticache")


def get_cloudwatch_client():
    """Devuelve un cliente CloudWatch para consultar metricas de ElastiCache."""
    return get_session().client("cloudwatch")


def get_clusters_dataframe(apply_tag_filter: bool = True):
    """Lista clusters de ElastiCache y los transforma en un DataFrame para la UI."""

    if get_mock_mode():
        from mocks.elasticache_mock import get_clusters_dataframe
        return get_clusters_dataframe()

    try:
        elasticache = get_elasticache_client()
        tag_filter = get_tag_filter() if apply_tag_filter else None

        clusters = elasticache.describe_cache_clusters(ShowCacheNodeInfo=True).get("CacheClusters", [])

        for c in clusters:
            arn = c.get("ARN")
            c["tags"] = []
            if arn:
                tag_list = elasticache.list_tags_for_resource(ResourceName=arn).get("TagList", [])
                c["tags"] = [{"Key": t.get("Key"), "Value": t.get("Value")} for t in tag_list]

        clusters = apply_tag_filter_to_list(clusters, tag_filter)

        rows = []
        for c in clusters:
            rows.append({
                "Cluster": c.get("CacheClusterId"),
                "Estado": c.get("CacheClusterStatus"),
                "Motor": c.get("Engine"),
                "Version": c.get("EngineVersion"),
                "Tipo de nodo": c.get("CacheNodeType"),
                "Nodos": c.get("NumCacheNodes"),
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "ElastiCache", "obtener clusters")
        return pd.DataFrame()


def get_replication_groups_dataframe(apply_tag_filter: bool = True):
    """Lista replication groups de ElastiCache y los transforma en DataFrame."""

    if get_mock_mode():
        from mocks.elasticache_mock import get_replication_groups_dataframe
        return get_replication_groups_dataframe()

    try:
        elasticache = get_elasticache_client()
        tag_filter = get_tag_filter() if apply_tag_filter else None

        groups = elasticache.describe_replication_groups().get("ReplicationGroups", [])

        for g in groups:
            arn = g.get("ARN")
            g["tags"] = []
            if arn:
                tag_list = elasticache.list_tags_for_resource(ResourceName=arn).get("TagList", [])
                g["tags"] = [{"Key": t.get("Key"), "Value": t.get("Value")} for t in tag_list]

        groups = apply_tag_filter_to_list(groups, tag_filter)

        rows = []
        for g in groups:
            rows.append({
                "Replication Group": g.get("ReplicationGroupId"),
                "Estado": g.get("Status"),
                "Cluster primario": g.get("PrimaryEndpoint", {}).get("Address"),
                "Miembros": len(g.get("MemberClusters", [])),
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "ElastiCache", "obtener replication groups")
        return pd.DataFrame()


def get_cpu_metrics(cache_cluster_id):
    """Consulta CPUUtilization en CloudWatch para un cluster de ElastiCache."""

    if get_mock_mode():
        from mocks.elasticache_mock import get_cpu_metrics
        return get_cpu_metrics(cache_cluster_id)

    try:
        cloudwatch = get_cloudwatch_client()

        end = datetime.utcnow()
        start = end - timedelta(minutes=30)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/ElastiCache",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "CacheClusterId", "Value": cache_cluster_id}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )

        rows = []
        for p in response.get("Datapoints", []):
            rows.append({"instante": p["Timestamp"], "cpu": p["Average"]})

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("instante")

        return df
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (ElastiCache)", f"obtener CPU del cluster {cache_cluster_id}")
        return pd.DataFrame()


def get_freeable_memory_metrics(cache_cluster_id):
    """Consulta FreeableMemory en CloudWatch para un cluster de ElastiCache."""

    if get_mock_mode():
        from mocks.elasticache_mock import get_freeable_memory_metrics
        return get_freeable_memory_metrics(cache_cluster_id)

    try:
        cloudwatch = get_cloudwatch_client()

        end = datetime.utcnow()
        start = end - timedelta(minutes=30)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/ElastiCache",
            MetricName="FreeableMemory",
            Dimensions=[{"Name": "CacheClusterId", "Value": cache_cluster_id}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Average"],
        )

        rows = []
        for p in response.get("Datapoints", []):
            memory_bytes = p["Average"]
            if memory_bytes >= 1024 ** 3:
                memory_value = round(memory_bytes / (1024 ** 3), 2)
                memory_unit = "GB"
            else:
                memory_value = round(memory_bytes / (1024 ** 2), 2)
                memory_unit = "MB"

            rows.append({
                "instante": p["Timestamp"],
                "memoria_libre": memory_value,
                "unidad_memoria": memory_unit,
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("instante")

        return df
    except Exception as exc:
        show_aws_error(
            exc,
            "CloudWatch (ElastiCache)",
            f"obtener memoria libre del cluster {cache_cluster_id}",
        )
        return pd.DataFrame()
