import pandas as pd
import random
from datetime import datetime, timedelta


def get_clusters_dataframe():

    rows = []

    engines = ["redis", "memcached"]
    for i in range(4):
        rows.append({
            "Cluster": f"cache-cluster-{i}",
            "Estado": "available",
            "Motor": random.choice(engines),
            "Version": random.choice(["7.1", "6.2", "1.6.22"]),
            "Tipo de nodo": random.choice(["cache.t3.micro", "cache.t4g.small", "cache.r6g.large"]),
            "Nodos": random.randint(1, 3),
        })

    return pd.DataFrame(rows)


def get_replication_groups_dataframe():

    rows = []

    for i in range(3):
        rows.append({
            "Replication Group": f"rg-{i}",
            "Estado": "available",
            "Cluster primario": f"rg-{i}.xxxxx.use1.cache.amazonaws.com",
            "Miembros": random.randint(1, 4),
        })

    return pd.DataFrame(rows)


def get_cpu_metrics(cache_cluster_id):

    rows = []

    now = datetime.utcnow()

    for i in range(30):
        rows.append({
            "instante": now - timedelta(minutes=i),
            "cpu": random.uniform(5, 75),
        })

    return pd.DataFrame(rows)


def get_freeable_memory_metrics(cache_cluster_id):

    rows = []

    now = datetime.utcnow()

    for i in range(30):
        memory_bytes = random.uniform(200_000_000, 2_000_000_000)
        if memory_bytes >= 1024 ** 3:
            memory_value = round(memory_bytes / (1024 ** 3), 2)
            memory_unit = "GB"
        else:
            memory_value = round(memory_bytes / (1024 ** 2), 2)
            memory_unit = "MB"

        rows.append({
            "instante": now - timedelta(minutes=i),
            "memoria_libre": memory_value,
            "unidad_memoria": memory_unit,
        })

    return pd.DataFrame(rows)
