import pandas as pd
import random
from datetime import datetime, timedelta


def get_tables_dataframe():
    now = datetime.utcnow()

    rows = [
        {
            "Nombre de Tabla": "usuarios",
            "Estado": "ACTIVE",
            "Tamaño (Bytes)": 1024000,
            "Elementos": 5430,
            "% de Lectura": "PAY_PER_REQUEST",
            "% de escritura": "PAY_PER_REQUEST",
            "Creada": now - timedelta(days=180)
        },
        {
            "Nombre de Tabla": "pedidos",
            "Estado": "ACTIVE",
            "Tamaño (Bytes)": 5242880,
            "Elementos": 12890,
            "% de Lectura": 100,
            "% de escritura": 50,
            "Creada": now - timedelta(days=365)
        },
        {
            "Nombre de Tabla": "productos",
            "Estado": "ACTIVE",
            "Tamaño (Bytes)": 2097152,
            "Elementos": 3200,
            "% de Lectura": 50,
            "% de escritura": 25,
            "Creada": now - timedelta(days=90)
        }
    ]

    dataframe = pd.DataFrame(rows)
    dataframe["Creada"] = pd.to_datetime(
        dataframe["Creada"],
        utc=True,
        errors="coerce",
    ).dt.tz_localize(None)

    return dataframe


def get_read_throughput_metrics(table_name):
    now = datetime.utcnow()

    rows = []

    for i in range(60):
        rows.append({
            "instante": now - timedelta(minutes=59 - i),
            "% de Lectura": random.uniform(10, 100)
        })

    return pd.DataFrame(rows)


def get_write_throughput_metrics(table_name):
    now = datetime.utcnow()

    rows = []

    for i in range(60):
        rows.append({
            "instante": now - timedelta(minutes=59 - i),
            "% de escritura": random.uniform(5, 50)
        })

    return pd.DataFrame(rows)


def get_throttled_requests_metrics(table_name):
    now = datetime.utcnow()

    rows = []

    for i in range(60):
        rows.append({
            "instante": now - timedelta(minutes=59 - i),
            "Conexiones": random.randint(0, 3)
        })

    return pd.DataFrame(rows)
