from config import get_mock_mode
from datetime import datetime, timedelta
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter, apply_tag_filter_to_list

import pandas as pd


def get_s3_client():
    """Devuelve un cliente S3 construido con la sesion AWS activa."""
    return get_session().client("s3")


def get_cloudwatch_client():
    """Devuelve un cliente CloudWatch para consultar metricas de S3."""
    return get_session().client("cloudwatch")


def get_buckets_dataframe(apply_tag_filter: bool = True):
    """Lista buckets S3 y los transforma en un DataFrame para la UI."""

    if get_mock_mode():
        from mocks.s3_mock import get_buckets_dataframe
        return get_buckets_dataframe()

    try:
        s3 = get_s3_client()
        tag_filter = get_tag_filter() if apply_tag_filter else None

        response = s3.list_buckets()
        buckets = response.get("Buckets", [])

        if not buckets:
            return pd.DataFrame()

        # list_buckets no devuelve tags
        for b in buckets:
            try:
                tag_response = s3.get_bucket_tagging(Bucket=b["Name"])
                b["tags"] = tag_response.get("TagSet", [])
            except s3.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchTagSet":
                    b["tags"] = []
                else:
                    raise

        buckets = apply_tag_filter_to_list(buckets, tag_filter)

        rows = []

        for b in buckets:
            # La región se obtiene aparte
            try:
                loc = s3.get_bucket_location(Bucket=b["Name"])
                region = loc["LocationConstraint"] or "us-east-1"
            except Exception:
                region = "N/A"

            rows.append({
                "Bucket": b["Name"],
                "Fecha de creación": b.get("CreationDate"),
                "Región": region,
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "S3", "obtener buckets")
        return pd.DataFrame()


def get_objects_dataframe(bucket_name, prefix=""):
    """Lista objetos de un bucket S3 (primer nivel o bajo un prefijo)."""

    if get_mock_mode():
        from mocks.s3_mock import get_objects_dataframe
        return get_objects_dataframe(bucket_name, prefix)

    try:
        s3 = get_s3_client()

        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(
            Bucket=bucket_name,
            Prefix=prefix,
            Delimiter="/",   # agrupa por "carpeta" virtual
        )

        rows = []

        for page in pages:
            # Prefijos comunes -> carpetas virtuales
            for cp in page.get("CommonPrefixes", []):
                rows.append({
                    "Nombre": cp["Prefix"],
                    "Tipo": "Carpeta",
                    "Tamaño (KB)": None,
                    "Última modificación": None,
                    "Clase de almacenamiento": None,
                })

            # Objetos reales
            for obj in page.get("Contents", []):
                # Omitir el propio prefijo si aparece como entrada
                if obj["Key"] == prefix:
                    continue
                rows.append({
                    "Nombre": obj["Key"],
                    "Tipo": "Objeto",
                    "Tamaño (KB)": round(obj["Size"] / 1024, 2),
                    "Última modificación": obj["LastModified"],
                    "Clase de almacenamiento": obj.get("StorageClass"),
                })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "S3", f"obtener objetos del bucket {bucket_name}")
        return pd.DataFrame()


def get_bucket_size_metrics(bucket_name):
    """Consulta BucketSizeBytes en CloudWatch (métrica diaria) para el bucket."""

    if get_mock_mode():
        from mocks.s3_mock import get_bucket_size_metrics
        return get_bucket_size_metrics(bucket_name)

    try:
        cloudwatch = get_cloudwatch_client()

        end = datetime.utcnow()
        # S3 publica esta métrica una vez al día
        start = end - timedelta(days=14)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/S3",
            MetricName="BucketSizeBytes",
            Dimensions=[
                {"Name": "BucketName", "Value": bucket_name},
                {"Name": "StorageType", "Value": "StandardStorage"},
            ],
            StartTime=start,
            EndTime=end,
            Period=86400,   # 1 día
            Statistics=["Average"],
        )

        rows = []

        for p in response.get("Datapoints", []):
            rows.append({
                "instante": p["Timestamp"],
                "tamaño_gb": round(p["Average"] / (1024 ** 3), 3),
            })

        df = pd.DataFrame(rows)

        if not df.empty:
            df = df.sort_values("instante")

        return df
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (S3)", f"obtener tamaño del bucket {bucket_name}")
        return pd.DataFrame()


def get_request_metrics(bucket_name):
    """Consulta NumberOfRequests en CloudWatch para el bucket indicado.

    Nota: esta métrica requiere que las métricas de solicitud estén habilitadas
    en la configuración del bucket (no vienen activas por defecto).
    """

    if get_mock_mode():
        from mocks.s3_mock import get_request_metrics
        return get_request_metrics(bucket_name)

    try:
        cloudwatch = get_cloudwatch_client()

        end = datetime.utcnow()
        start = end - timedelta(hours=24)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/S3",
            MetricName="NumberOfObjects",
            Dimensions=[
                {"Name": "BucketName", "Value": bucket_name},
                {"Name": "StorageType", "Value": "AllStorageTypes"},
            ],
            StartTime=start,
            EndTime=end,
            Period=3600,    # 1 hora
            Statistics=["Average"],
        )

        rows = []

        for p in response.get("Datapoints", []):
            rows.append({
                "instante": p["Timestamp"],
                "objetos": int(p["Average"]),
            })

        df = pd.DataFrame(rows)

        if not df.empty:
            df = df.sort_values("instante")

        return df
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (S3)", f"obtener número de objetos del bucket {bucket_name}")
        return pd.DataFrame()
