import pandas as pd
import random
from datetime import datetime, timedelta, timezone


def get_buckets_dataframe():

    regions = ["eu-west-1", "us-east-1", "us-west-2", "ap-southeast-1"]
    rows = []

    for i in range(5):
        rows.append({
            "Bucket": f"mi-bucket-{i}",
            "Fecha de creación": datetime.now(timezone.utc) - timedelta(days=random.randint(30, 730)),
            "Región": random.choice(regions),
        })

    return pd.DataFrame(rows)


def get_objects_dataframe(bucket_name, prefix=""):

    rows = []

    # Simular dos carpetas virtuales
    for i in range(2):
        rows.append({
            "Nombre": f"{prefix}carpeta-{i}/",
            "Tipo": "Carpeta",
            "Tamaño (KB)": None,
            "Última modificación": None,
            "Clase de almacenamiento": None,
        })

    storage_classes = ["STANDARD", "STANDARD_IA", "GLACIER"]

    for i in range(random.randint(3, 8)):
        rows.append({
            "Nombre": f"{prefix}archivo-{i}.txt",
            "Tipo": "Objeto",
            "Tamaño (KB)": round(random.uniform(1, 10240), 2),
            "Última modificación": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90)),
            "Clase de almacenamiento": random.choice(storage_classes),
        })

    return pd.DataFrame(rows)


def get_bucket_size_metrics(bucket_name):

    rows = []
    now = datetime.now(timezone.utc)
    size_gb = random.uniform(1, 50)

    for i in range(14):
        size_gb += random.uniform(-0.5, 1.5)
        rows.append({
            "instante": now - timedelta(days=14 - i),
            "tamaño_gb": round(max(size_gb, 0), 3),
        })

    return pd.DataFrame(rows)


def get_request_metrics(bucket_name):

    rows = []
    now = datetime.now(timezone.utc)
    n_objects = random.randint(100, 5000)

    for i in range(24):
        n_objects += random.randint(-10, 20)
        rows.append({
            "instante": now - timedelta(hours=24 - i),
            "objetos": max(n_objects, 0),
        })

    return pd.DataFrame(rows)