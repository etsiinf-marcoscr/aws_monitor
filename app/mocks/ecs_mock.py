import pandas as pd
import random
from datetime import datetime, timedelta


def get_clusters_dataframe():

    rows = []

    for i in range(3):

        rows.append({
            "Cluster": f"cluster-{i}",
            "Estado": "ACTIVE",
            "Tareas en ejecución": random.randint(5,20),
            "Tareas pendientes": random.randint(0,3),
            "Servicios": random.randint(2,6),
            "Instancias de contenedores": random.randint(2,10)
        })

    return pd.DataFrame(rows)


def get_services_dataframe(cluster_name):

    rows = []

    for i in range(4):

        rows.append({
            "Service": f"{cluster_name}-service-{i}",
            "Estado": "ACTIVE",
            "Tipo de lanzamiento": "FARGATE",
            "Tareas deseadas": random.randint(1,5),
            "Tareas en ejecución": random.randint(1,5),
            "Tareas pendientes": random.randint(0,1),
            "Definición de Tarea": f"task-def-{i}"
        })

    return pd.DataFrame(rows)


def get_tasks_dataframe(cluster_name, service_name):

    rows = []

    for i in range(random.randint(2,5)):

        rows.append({
            "ARN de Tarea": f"task-{i}",
            "Estado": "RUNNING",
            "CPU": "256",
            "Memoria (MB)": "512",
            "Tipo de lanzamiento": "FARGATE",
            "Fecha de comienzo": datetime.utcnow() - timedelta(minutes=random.randint(1,60))
        })

    dataframe = pd.DataFrame(rows)
    dataframe["Fecha de comienzo"] = pd.to_datetime(
        dataframe["Fecha de comienzo"],
        utc=True,
        errors="coerce",
    ).dt.tz_localize(None)

    return dataframe


def get_cpu_metrics(cluster_name, service_name):

    rows = []

    now = datetime.utcnow()

    for i in range(30):

        rows.append({
            "instante": now - timedelta(minutes=i),
            "cpu": random.uniform(10,80)
        })

    return pd.DataFrame(rows)


def get_memory_metrics(cluster_name, service_name):

    rows = []

    now = datetime.utcnow()

    for i in range(30):

        rows.append({
            "instante": now - timedelta(minutes=i),
            "memoria": random.uniform(20,90)
        })

    return pd.DataFrame(rows)