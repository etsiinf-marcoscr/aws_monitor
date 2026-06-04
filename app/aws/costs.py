from config import get_mock_mode
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter
import pandas as pd


# Servicios del stack de contenedores que monitorizamos
MONITORED_SERVICES = [
    "Amazon Elastic Container Service",
    "Amazon EC2 Container Registry (ECR)",
    "Amazon Relational Database Service",
    "Amazon DynamoDB",
    "Amazon Simple Storage Service",
    "Amazon CloudFront",
    "Amazon Cognito",
    "Amazon Simple Notification Service",
    "Amazon Simple Queue Service",
    "Amazon ElastiCache",
    "AWS WAF",
    "AWS Key Management Service",
]


def _current_month_period() -> dict:
    """Devuelve el periodo desde el primer día del mes actual hasta hoy."""
    today = pd.Timestamp.now()
    start = today.replace(day=1).strftime("%Y-%m-%d")
    # Cost Explorer requiere que End sea un día posterior al último dato
    end = (today + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    return {"Start": start, "End": end}


def _build_tag_filter(tag_filter: dict | None) -> dict | None:
    """Construye el filtro de Cost Explorer para tag + servicios monitorizados."""
    service_filter = {
        "Dimensions": {
            "Key": "SERVICE",
            "Values": MONITORED_SERVICES,
        }
    }

    if tag_filter is None:
        return service_filter

    return {
        "And": [
            service_filter,
            {
                "Tags": {
                    "Key": tag_filter["key"],
                    "Values": [tag_filter["value"]],
                }
            },
        ]
    }


def estimate_costs() -> pd.DataFrame:
    """
    Consulta Cost Explorer y devuelve costes del mes actual agrupados por servicio.
    Si hay un filtro de tag activo, restringe los resultados a recursos con esa etiqueta.
    """

    if get_mock_mode():
        from mocks.costs_mock import estimate_costs
        return estimate_costs()

    try:
        ce = get_session().client("ce")
        tag_filter = get_tag_filter()

        response = ce.get_cost_and_usage(
            TimePeriod=_current_month_period(),
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            Filter=_build_tag_filter(tag_filter),
        )

        groups = response.get("ResultsByTime", [{}])[0].get("Groups", [])
        rows = []

        for g in groups:
            cost = float(g["Metrics"]["UnblendedCost"]["Amount"])
            if cost > 0:
                rows.append({
                    "Servicio": g["Keys"][0],
                    "Coste mensual ($)": round(cost, 2),
                })

        return pd.DataFrame(rows).sort_values("Coste mensual ($)", ascending=False)
    except Exception as exc:
        show_aws_error(exc, "Cost Explorer", "obtener costes")
        return pd.DataFrame()


def estimate_costs_by_day() -> pd.DataFrame:
    """
    Devuelve la evolución diaria de costes del mes actual.
    Útil para el gráfico de tendencia en la página de costes.
    """

    if get_mock_mode():
        from mocks.costs_mock import estimate_costs_by_day
        return estimate_costs_by_day()

    try:
        ce = get_session().client("ce")
        tag_filter = get_tag_filter()

        response = ce.get_cost_and_usage(
            TimePeriod=_current_month_period(),
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            Filter=_build_tag_filter(tag_filter),
        )

        rows = []
        accumulated = 0.0

        for result in response.get("ResultsByTime", []):
            daily = float(result["Total"]["UnblendedCost"]["Amount"])
            accumulated += daily
            rows.append({
                "Fecha": result["TimePeriod"]["Start"],
                "Coste diario ($)": round(daily, 2),
                "Coste acumulado ($)": round(accumulated, 2),
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "Cost Explorer", "obtener evolución diaria de costes")
        return pd.DataFrame()