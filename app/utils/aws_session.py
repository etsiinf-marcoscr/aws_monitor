import os

import boto3
import streamlit as st


def _get_aws_value(session_key, env_name, default_value=""):
    """Devuelve un valor AWS con prioridad: session_state -> entorno -> default."""
    value = st.session_state.get(session_key)

    if value:
        return value

    env_value = os.getenv(env_name)

    if env_value:
        return env_value

    if default_value:
        return default_value

    return None


def get_session():
    """Crea una sesion boto3 usando credenciales cargadas en la UI o en .env."""
    return boto3.Session(
        aws_access_key_id=_get_aws_value("aws_access_key_id", "AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=_get_aws_value("aws_secret_access_key", "AWS_SECRET_ACCESS_KEY"),
        aws_session_token=_get_aws_value("aws_session_token", "AWS_SESSION_TOKEN"),
        region_name=_get_aws_value("aws_region", "AWS_DEFAULT_REGION", "us-east-1"),
    )


def get_clients():
    """Construye un diccionario con clientes AWS reutilizando una misma sesion."""
    session = get_session()

    return {
        "ecs": session.client("ecs"),
        "ecr": session.client("ecr"),
        "rds": session.client("rds"),
        "ec2": session.client("ec2"),
        "iam": session.client("iam"),
        "ce": session.client("ce"),
        "cloudformation": session.client("cloudformation"),
        "cloudwatch": session.client("cloudwatch"),
    }