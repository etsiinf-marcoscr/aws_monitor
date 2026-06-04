from config import get_mock_mode
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter, apply_tag_filter_to_list
import pandas as pd


def get_sqs_client():
    return get_session().client("sqs")


def get_cloudwatch_client():
    return get_session().client("cloudwatch")


def get_queues_dataframe(apply_tag_filter: bool = True):
    """Lista colas SQS y devuelve DataFrame con atributos básicos."""

    if get_mock_mode():
        from mocks.sqs_mock import get_queues_dataframe
        return get_queues_dataframe()

    try:
        client = get_sqs_client()
        tag_filter = get_tag_filter() if apply_tag_filter else None

        queue_urls = client.list_queues().get("QueueUrls", [])
        rows = []

        for url in queue_urls:
            name = url.split("/")[-1]

            # QueueArn es necesario para list_queue_tags cuando hay filtro activo
            attr_names = [
                "ApproximateNumberOfMessages",
                "ApproximateNumberOfMessagesNotVisible",
            ]
            if tag_filter:
                attr_names.append("QueueArn")

            try:
                attrs = client.get_queue_attributes(
                    QueueUrl=url,
                    AttributeNames=attr_names,
                ).get("Attributes", {})
            except Exception:
                attrs = {}

            if tag_filter:
                queue_arn = attrs.get("QueueArn", "")
                try:
                    # SQS devuelve tags como dict {"key": "value"}
                    raw_tags = client.list_queue_tags(QueueUrl=url).get("Tags", {})
                    tags = [{"Key": k, "Value": v} for k, v in raw_tags.items()]
                except Exception:
                    tags = []

                # Construimos un objeto temporal para apply_tag_filter_to_list
                proxy = {"tags": tags}
                if not apply_tag_filter_to_list([proxy], tag_filter):
                    continue

            rows.append({
                "URL de Cola": url,
                "Nombre": name,
                "Mensajes Visibles Aprox.": int(attrs.get("ApproximateNumberOfMessages", 0)),
                "Mensajes No Visibles Aprox.": int(attrs.get("ApproximateNumberOfMessagesNotVisible", 0)),
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "SQS", "obtener colas")
        return pd.DataFrame()


def get_queue_attributes_dataframe(queue_url):
    """Devuelve atributos completos de una cola SQS."""

    if get_mock_mode():
        from mocks.sqs_mock import get_queue_attributes_dataframe
        return get_queue_attributes_dataframe(queue_url)

    try:
        client = get_sqs_client()

        attrs = client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=["All"],
        ).get("Attributes", {})

        rows = [{"Atributo": k, "Valor": v} for k, v in attrs.items()]

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "SQS", f"obtener atributos de {queue_url}")
        return pd.DataFrame()


def _get_metric_dataframe(metric_name, queue_name):
    """Helper para consultar métricas CloudWatch para una cola (última hora)."""

    try:
        cloudwatch = get_cloudwatch_client()
        from datetime import datetime, timedelta

        end = datetime.utcnow()
        start = end - timedelta(minutes=60)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/SQS",
            MetricName=metric_name,
            Dimensions=[{"Name": "QueueName", "Value": queue_name}],
            StartTime=start,
            EndTime=end,
            Period=60,
            Statistics=["Sum"],
        )

        rows = []
        for p in response.get("Datapoints", []):
            rows.append({"instante": p["Timestamp"], "value": p.get("Sum")})

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("instante")
        return df
    except Exception as exc:
        show_aws_error(exc, "CloudWatch (SQS)", f"obtener métrica {metric_name} para {queue_name}")
        return pd.DataFrame()


def get_messages_sent_metrics(queue_name):
    if get_mock_mode():
        from mocks.sqs_mock import get_messages_sent_metrics
        return get_messages_sent_metrics(queue_name)
    return _get_metric_dataframe("NumberOfMessagesSent", queue_name).rename(columns={"value": "Mensajes Enviados"})


def get_messages_received_metrics(queue_name):
    if get_mock_mode():
        from mocks.sqs_mock import get_messages_received_metrics
        return get_messages_received_metrics(queue_name)
    return _get_metric_dataframe("NumberOfMessagesReceived", queue_name).rename(columns={"value": "Mensajes Recibidos"})


def get_messages_deleted_metrics(queue_name):
    if get_mock_mode():
        from mocks.sqs_mock import get_messages_deleted_metrics
        return get_messages_deleted_metrics(queue_name)
    return _get_metric_dataframe("NumberOfMessagesDeleted", queue_name).rename(columns={"value": "Mensajes Eliminados"})
