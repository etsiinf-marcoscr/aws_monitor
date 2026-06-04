import pandas as pd
import random
from datetime import datetime, timedelta


def get_topics_dataframe():
    now = datetime.utcnow()

    rows = [
        {"ARN del Tema": "arn:aws:sns:eu-west-1:123456789012:alerts", "Nombre": "alerts", "Suscripciones": 3},
        {"ARN del Tema": "arn:aws:sns:eu-west-1:123456789012:deploys", "Nombre": "deploys", "Suscripciones": 1}
    ]

    return pd.DataFrame(rows)


def get_subscriptions_dataframe(topic_arn):
    if topic_arn.endswith("alerts"):
        rows = [
            {"ARN de Suscripción": "arn:aws:sns:...:sub1", "Protocolo": "email", "Punto de Entrada": "ops@example.com", "Propietario": "123456789012"},
            {"ARN de Suscripción": "arn:aws:sns:...:sub2", "Protocolo": "https", "Punto de Entrada": "https://hooks.example.com/sns", "Propietario": "123456789012"},
            {"ARN de Suscripción": "arn:aws:sns:...:sub3", "Protocolo": "sms", "Punto de Entrada": "+1234567890", "Propietario": "123456789012"}
        ]
    else:
        rows = [
            {"ARN de Suscripción": "arn:aws:sns:...:sub4", "Protocolo": "email", "Punto de Entrada": "deploys@example.com", "Propietario": "123456789012"}
        ]

    return pd.DataFrame(rows)


def get_publish_metrics(topic_arn):
    now = datetime.utcnow()

    rows = []

    for i in range(60):
        rows.append({
            "instante": now - timedelta(minutes=59 - i),
            "Publicaciones": random.randint(0, 10)
        })

    return pd.DataFrame(rows)
