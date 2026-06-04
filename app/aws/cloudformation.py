from config import get_mock_mode
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session
import pandas as pd
import json


def get_stacks_dataframe():
    """Lista stacks de CloudFormation y devuelve un resumen en DataFrame."""

    if get_mock_mode():
        from mocks.cloudformation_mock import get_stacks_dataframe
        return get_stacks_dataframe()

    try:
        cf = get_session().client("cloudformation")

        stacks = cf.describe_stacks().get("Stacks", [])

        rows = []

        for stack in stacks:

            rows.append({
                "Nombre del despliegue": stack["StackName"],
                "Estado": stack["StackStatus"],
                "Fecha de creación": stack["CreationTime"]
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "CloudFormation", "obtener stacks")
        return pd.DataFrame()


def get_stack_overview(stack_name):
    """Devuelve los datos clave de un stack concreto."""

    if get_mock_mode():
        from mocks.cloudformation_mock import get_stack_overview
        return get_stack_overview(stack_name)

    try:
        cf = get_session().client("cloudformation")
        stack = cf.describe_stacks(StackName=stack_name).get("Stacks", [])[0]

        outputs = stack.get("Outputs", [])
        tags = stack.get("Tags", [])
        drift = stack.get("DriftInformation", {})

        return {
            "Nombre del despliegue": stack.get("StackName"),
            "Estado": stack.get("StackStatus"),
            "Descripción": stack.get("Description", ""),
            "Fecha de creación": stack.get("CreationTime"),
            "Fecha de última actualización": stack.get("LastUpdatedTime"),
            "Protección ante eliminación": stack.get("EnableTerminationProtection", False),
            "Estado de drift": drift.get("StackDriftStatus", "UNKNOWN"),
            "Número de salidas": len(outputs),
            "Número de etiquetas": len(tags),
            "Tags": tags,
            "Outputs": outputs,
        }
    except Exception as exc:
        show_aws_error(exc, "CloudFormation", f"obtener resumen de {stack_name}")
        return {}


def get_stack_resources_dataframe(stack_name):
    """Devuelve los recursos de un stack en DataFrame."""

    if get_mock_mode():
        from mocks.cloudformation_mock import get_stack_resources_dataframe
        return get_stack_resources_dataframe(stack_name)

    try:
        cf = get_session().client("cloudformation")
        resources = cf.describe_stack_resources(StackName=stack_name).get("StackResources", [])

        rows = []
        for resource in resources:
            rows.append({
                "ID lógico": resource.get("LogicalResourceId"),
                "ID físico": resource.get("PhysicalResourceId"),
                "Tipo": resource.get("ResourceType"),
                "Estado": resource.get("ResourceStatus"),
                "Razón estado": resource.get("ResourceStatusReason", ""),
                "Timestamp": resource.get("Timestamp"),
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "CloudFormation", f"obtener recursos de {stack_name}")
        return pd.DataFrame()


def get_stack_template(stack_name):
    """Devuelve el template del stack como texto JSON formateado."""

    if get_mock_mode():
        from mocks.cloudformation_mock import get_stack_template
        return get_stack_template(stack_name)

    try:
        cf = get_session().client("cloudformation")
        body = cf.get_template(StackName=stack_name, TemplateStage="Original").get("TemplateBody")

        if isinstance(body, dict):
            return json.dumps(body, indent=2, default=str)

        return str(body or "")
    except Exception as exc:
        show_aws_error(exc, "CloudFormation", f"obtener template de {stack_name}")
        return ""


def get_stack_events_dataframe(stack_name, limit=50):
    """Devuelve los eventos recientes de un stack en DataFrame."""

    if get_mock_mode():
        from mocks.cloudformation_mock import get_stack_events_dataframe
        return get_stack_events_dataframe(stack_name, limit=limit)

    try:
        cf = get_session().client("cloudformation")
        events = cf.describe_stack_events(StackName=stack_name).get("StackEvents", [])

        rows = []
        for event in events[:limit]:
            rows.append({
                "Timestamp": event.get("Timestamp"),
                "ID lógico": event.get("LogicalResourceId"),
                "ID físico": event.get("PhysicalResourceId"),
                "Tipo": event.get("ResourceType"),
                "Estado": event.get("ResourceStatus"),
                "Razón": event.get("ResourceStatusReason", ""),
            })

        return pd.DataFrame(rows)
    except Exception as exc:
        show_aws_error(exc, "CloudFormation", f"obtener eventos de {stack_name}")
        return pd.DataFrame()
