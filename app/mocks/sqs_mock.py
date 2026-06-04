import pandas as pd
import random
from datetime import datetime, timedelta


def get_queues_dataframe():
    rows = [
        {"URL de Cola": "https://sqs.eu-west-1.amazonaws.com/123456789012/alerts-queue", "Nombre": "alerts-queue", "Mensajes Visibles Aprox.": 5, "Mensajes No Visibles Aprox.": 0},
        {"URL de Cola": "https://sqs.eu-west-1.amazonaws.com/123456789012/tasks-queue", "Nombre": "tasks-queue", "Mensajes Visibles Aprox.": 2, "Mensajes No Visibles Aprox.": 1}
    ]
    return pd.DataFrame(rows)


def get_queue_attributes_dataframe(queue_url):
    return pd.DataFrame([
        {"Atributo": "VisibilityTimeout", "Valor": "30"},
        {"Atributo": "ApproximateNumberOfMessages", "Valor": "5"},
        {"Atributo": "DelaySeconds", "Valor": "0"}
    ])


def _metrics_template():
    now = datetime.utcnow()
    rows = []
    for i in range(60):
        rows.append({
            "instante": now - timedelta(minutes=59 - i),
            "value": random.randint(0, 10)
        })
    return pd.DataFrame(rows)


def get_messages_sent_metrics(queue_name):
    return _metrics_template().rename(columns={"value": "Mensajes Enviados"})


def get_messages_received_metrics(queue_name):
    return _metrics_template().rename(columns={"value": "Mensajes Recibidos"})


def get_messages_deleted_metrics(queue_name):
    return _metrics_template().rename(columns={"value": "Mensajes Eliminados"})
