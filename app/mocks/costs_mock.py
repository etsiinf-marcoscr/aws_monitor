import pandas as pd
import random


# Basado en el día del mes para que varíe cada día pero sea consistente durante el mismo día
_SEED = pd.Timestamp.now().day
random.seed(_SEED)


def _rand(base, variance=0.25):
    """Devuelve un valor aleatorio en torno a base con la varianza indicada."""
    delta = base * variance
    return round(random.uniform(base - delta, base + delta), 2)


def estimate_costs():
    """Datos simulados de costes con variación aleatoria por día."""

    rows = [
        {"Servicio": "Amazon Elastic Container Service",       "Coste mensual ($)": _rand(42.50)},
        {"Servicio": "Amazon EC2 Container Registry (ECR)",    "Coste mensual ($)": _rand(3.20)},
        {"Servicio": "Amazon Relational Database Service",     "Coste mensual ($)": _rand(67.80)},
        {"Servicio": "Amazon DynamoDB",                        "Coste mensual ($)": _rand(18.40)},
        {"Servicio": "Amazon Simple Storage Service",          "Coste mensual ($)": _rand(9.75)},
        {"Servicio": "Amazon CloudFront",                      "Coste mensual ($)": _rand(5.30)},
        {"Servicio": "Amazon Cognito",                         "Coste mensual ($)": _rand(2.10)},
        {"Servicio": "Amazon Simple Notification Service",     "Coste mensual ($)": _rand(1.40)},
        {"Servicio": "Amazon Simple Queue Service",            "Coste mensual ($)": _rand(0.95)},
        {"Servicio": "Amazon ElastiCache",                     "Coste mensual ($)": _rand(22.60)},
        {"Servicio": "AWS WAF",                                "Coste mensual ($)": _rand(8.00)},
        {"Servicio": "AWS Key Management Service",             "Coste mensual ($)": _rand(1.20)},
    ]

    return pd.DataFrame(rows)


def estimate_costs_by_day():
    """Datos simulados de evolución diaria de costes para el mes actual."""
    today = pd.Timestamp.now()
    days = pd.date_range(start=today.replace(day=1), end=today, freq="D")

    rows = []
    accumulated = 0.0
    for day in days:
        daily = round(random.uniform(4.5, 9.5), 2)
        accumulated += daily
        rows.append({
            "Fecha": day.date(),
            "Coste diario ($)": daily,
            "Coste acumulado ($)": round(accumulated, 2),
        })

    return pd.DataFrame(rows)