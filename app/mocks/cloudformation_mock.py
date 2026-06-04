import pandas as pd
from datetime import datetime
import json


def get_stacks_dataframe():

    rows = [
        {
            "Nombre del despliegue": "ecs-demo-stack",
            "Estado": "CREATE_COMPLETE",
            "Fecha de creación": datetime(2024, 2, 10)
        },
        {
            "Nombre del despliegue": "rds-test-stack",
            "Estado": "UPDATE_COMPLETE",
            "Fecha de creación": datetime(2024, 3, 1)
        }
    ]

    return pd.DataFrame(rows)


def get_stack_overview(stack_name):
    data = {
        "ecs-demo-stack": {
            "Nombre del despliegue": "ecs-demo-stack",
            "Estado": "CREATE_COMPLETE",
            "Descripción": "Despliegue demo de ECS con balanceador y red dedicada",
            "Fecha de creación": datetime(2024, 2, 10, 11, 20),
            "Fecha de última actualización": datetime(2024, 2, 10, 11, 45),
            "Protección ante eliminación": True,
            "Estado de drift": "IN_SYNC",
            "Número de salidas": 2,
            "Número de etiquetas": 2,
            "Tags": [{"Key": "env", "Value": "demo"}, {"Key": "owner", "Value": "platform"}],
            "Outputs": [
                {"OutputKey": "LoadBalancerDNS", "OutputValue": "ecs-demo-alb-123.eu-west-1.elb.amazonaws.com"},
                {"OutputKey": "ClusterName", "OutputValue": "ecs-demo-cluster"},
            ],
        },
        "rds-test-stack": {
            "Nombre del despliegue": "rds-test-stack",
            "Estado": "UPDATE_COMPLETE",
            "Descripción": "Stack de base de datos para entorno de test",
            "Fecha de creación": datetime(2024, 3, 1, 9, 0),
            "Fecha de última actualización": datetime(2024, 4, 4, 16, 30),
            "Protección ante eliminación": False,
            "Estado de drift": "IN_SYNC",
            "Número de salidas": 1,
            "Número de etiquetas": 1,
            "Tags": [{"Key": "env", "Value": "test"}],
            "Outputs": [{"OutputKey": "DBEndpoint", "OutputValue": "rds-test.xxxxxx.eu-west-1.rds.amazonaws.com"}],
        },
    }

    return data.get(stack_name, {})


def get_stack_resources_dataframe(stack_name):
    resources_by_stack = {
        "ecs-demo-stack": [
            {
                "ID lógico": "DemoVpc",
                "ID físico": "vpc-0123abcd",
                "Tipo": "AWS::EC2::VPC",
                "Estado": "CREATE_COMPLETE",
                "Razón estado": "",
                "Timestamp": datetime(2024, 2, 10, 11, 25),
            },
            {
                "ID lógico": "DemoService",
                "ID físico": "arn:aws:ecs:eu-west-1:111111111111:service/demo",
                "Tipo": "AWS::ECS::Service",
                "Estado": "CREATE_COMPLETE",
                "Razón estado": "",
                "Timestamp": datetime(2024, 2, 10, 11, 40),
            },
        ],
        "rds-test-stack": [
            {
                "ID lógico": "MainDatabase",
                "ID físico": "rds-test-instance-1",
                "Tipo": "AWS::RDS::DBInstance",
                "Estado": "UPDATE_COMPLETE",
                "Razón estado": "",
                "Timestamp": datetime(2024, 4, 4, 16, 25),
            }
        ],
    }

    return pd.DataFrame(resources_by_stack.get(stack_name, []))


def get_stack_template(stack_name):
    templates = {
        "ecs-demo-stack": {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Demo ECS stack",
            "Resources": {
                "DemoVpc": {"Type": "AWS::EC2::VPC"},
                "DemoCluster": {"Type": "AWS::ECS::Cluster"},
                "DemoService": {"Type": "AWS::ECS::Service"},
            },
        },
        "rds-test-stack": {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "RDS stack for tests",
            "Resources": {
                "MainDatabase": {"Type": "AWS::RDS::DBInstance"}
            },
        },
    }
    return json.dumps(templates.get(stack_name, {}), indent=2)


def get_stack_events_dataframe(stack_name, limit=50):
    events_by_stack = {
        "ecs-demo-stack": [
            {
                "Timestamp": datetime(2024, 2, 10, 11, 45),
                "ID lógico": "ecs-demo-stack",
                "ID físico": "ecs-demo-stack",
                "Tipo": "AWS::CloudFormation::Stack",
                "Estado": "CREATE_COMPLETE",
                "Razón": "",
            },
            {
                "Timestamp": datetime(2024, 2, 10, 11, 40),
                "ID lógico": "DemoService",
                "ID físico": "arn:aws:ecs:eu-west-1:111111111111:service/demo",
                "Tipo": "AWS::ECS::Service",
                "Estado": "CREATE_COMPLETE",
                "Razón": "",
            },
        ],
        "rds-test-stack": [
            {
                "Timestamp": datetime(2024, 4, 4, 16, 30),
                "ID lógico": "rds-test-stack",
                "ID físico": "rds-test-stack",
                "Tipo": "AWS::CloudFormation::Stack",
                "Estado": "UPDATE_COMPLETE",
                "Razón": "",
            }
        ],
    }

    return pd.DataFrame(events_by_stack.get(stack_name, [])[:limit])
