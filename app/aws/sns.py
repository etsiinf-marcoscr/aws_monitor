from config import get_mock_mode
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter, apply_tag_filter_to_list
import pandas as pd


def get_sns_client():
    """Devuelve un cliente SNS."""
    return get_session().client("sns")


def get_cloudwatch_client():
    return get_session().client("cloudwatch")


def get_topics_dataframe(apply_tag_filter: bool = True):
    """Lista topics SNS y devuelve DataFrame con información básica."""

    if get_mock_mode():
        from mocks.sns_mock import get_topics_dataframe
        return get_topics_dataframe()

    try:
        client = get_sns_client()
        tag_filter = get_tag_filter() if apply_tag_filter else None

        response = client.list_topics()
        topics = response.get("Topics", [])

        if tag_filter:
            # list_topics no soporta filtrado por tag
            for t in topics:
                try:
                    t["tags"] = client.list_tags_for_resource(
                        ResourceArn=t["TopicArn"]
                    ).get("Tags", [])
                except Exception:
                    t["tags"] = []

            topics = apply_tag_filter_to_list(topics, tag_filter)

        rows = []

        for t in topics:
            arn = t.get("TopicArn")
            name = arn.split(":")[-1] if arn else ""

            try:
                subs_count = len(
                    client.list_subscriptions_by_topic(TopicArn=arn).get("Subscriptions", [])
                )
            except Exception:
                subs_count = None

            rows.append({
                "ARN del Tema": arn,
                "Nombre": name,
                "Suscripciones": subs_count,
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "SNS", "obtener topics")
        return pd.DataFrame()


def get_subscriptions_dataframe(topic_arn):
    """Lista suscripciones de un topic SNS."""

    if get_mock_mode():
        from mocks.sns_mock import get_subscriptions_dataframe
        return get_subscriptions_dataframe(topic_arn)

    try:
        client = get_sns_client()

        subs = client.list_subscriptions_by_topic(
            TopicArn=topic_arn
        ).get("Subscriptions", [])

        rows = []

        for s in subs:
            rows.append({
                "ARN de Suscripción": s.get("SubscriptionArn"),
                "Protocolo": s.get("Protocol"),
                "Punto de Entrada": s.get("Endpoint"),
                "Propietario": s.get("Owner"),
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "SNS", f"obtener suscripciones del topic {topic_arn}")
        return pd.DataFrame()


def get_publish_metrics(topic_arn):
    """Consulta CloudWatch NumberOfMessagesPublished para el topic (última hora)."""

    if get_mock_mode():
        from mocks.sns_mock import get_publish_metrics
        return get_publish_metrics(topic_arn)

    try:
        cloudwatch = get_cloudwatch_client()

        from datetime import datetime, timedelta

        end = datetime.utcnow()
        start = end - timedelta(minutes=60)

        topic_name = topic_arn.split(":")[-1]

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/SNS",
            MetricName="NumberOfMessagesPublished",
            Dimensions=[{"Name": "TopicName", "Value": topic_name}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Sum"],
        )

        rows = []

        for p in response.get("Datapoints", []):
            rows.append({
                "instante": p["Timestamp"],
                "Publicaciones": p.get("Sum"),
            })

        df = pd.DataFrame(rows)

        if not df.empty:
            df = df.sort_values("instante")

        return df
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (SNS)", f"obtener métricas para {topic_arn}")
        return pd.DataFrame()
