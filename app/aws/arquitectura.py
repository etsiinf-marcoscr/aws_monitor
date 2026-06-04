"""
aws/arquitectura.py
Recopila conexiones entre servicios AWS para generar el grafo de arquitectura.
Las conexiones se infieren a partir de la configuración real de los recursos.
"""

from config import get_mock_mode
from utils.aws_errors import show_aws_error
from utils.aws_session import get_session

def _client(service):
    return get_session().client(service)

def _node(id, label, tipo):
    """Crea un nodo del grafo."""
    return {"id": id, "label": label, "tipo": tipo}


def _edge(source, target, label=""):
    """Crea una arista del grafo."""
    return {"source": source, "target": target, "label": label}

def _get_cloudfront_data(nodes, edges):
    """CloudFront -> S3 (orígenes) y CloudFront -> ALB (orígenes personalizados)."""
    try:
        cf = _client("cloudfront")
        distributions = cf.list_distributions().get("DistributionList", {}).get("Items", [])

        for dist in distributions:
            dist_id = dist["Id"]
            domain = dist.get("DomainName", dist_id)
            cf_node_id = f"cf_{dist_id}"
            nodes[cf_node_id] = _node(cf_node_id, f"CloudFront\\n{domain[:20]}", "cloudfront")

            for origin in dist.get("Origins", {}).get("Items", []):
                domain_name = origin.get("DomainName", "")

                # Origen S3
                if ".s3." in domain_name or domain_name.endswith(".s3.amazonaws.com"):
                    bucket = domain_name.split(".s3.")[0]
                    s3_node_id = f"s3_{bucket}"
                    nodes[s3_node_id] = _node(s3_node_id, f"S3\\n{bucket[:20]}", "s3")
                    edges.append(_edge(cf_node_id, s3_node_id, "origen"))

                # Origen ALB
                elif "elb.amazonaws.com" in domain_name:
                    alb_name = domain_name.split(".")[0]
                    alb_node_id = f"alb_{alb_name}"
                    nodes[alb_node_id] = _node(alb_node_id, f"ALB\\n{alb_name[:20]}", "alb")
                    edges.append(_edge(cf_node_id, alb_node_id, "origen"))

        # WAF asociado a CloudFront
        try:
            waf = _client("wafv2")
            acls = waf.list_web_acls(Scope="CLOUDFRONT").get("WebACLs", [])
            for acl in acls:
                waf_node_id = f"waf_{acl['Id']}"
                nodes[waf_node_id] = _node(waf_node_id, f"WAF\\n{acl['Name'][:20]}", "waf")
                for node_id in list(nodes.keys()):
                    if node_id.startswith("cf_"):
                        edges.append(_edge(waf_node_id, node_id, "protege"))
        except Exception:
            pass

    except Exception as exc:
        show_aws_error(exc, "CloudFront", "obtener distribuciones para grafo")


def _get_alb_ecs_connections(nodes, edges):
    """ALB -> ECS: target groups que apuntan a servicios ECS."""
    try:
        elbv2 = _client("elbv2")
        ecs = _client("ecs")

        lbs = elbv2.describe_load_balancers().get("LoadBalancers", [])

        for lb in lbs:
            lb_name = lb["LoadBalancerName"]
            alb_node_id = f"alb_{lb_name}"
            if alb_node_id not in nodes:
                nodes[alb_node_id] = _node(alb_node_id, f"ALB\\n{lb_name[:20]}", "alb")

        # Buscar servicios ECS con load balancer configurado
        cluster_arns = ecs.list_clusters().get("clusterArns", [])
        for cluster_arn in cluster_arns:
            cluster_name = cluster_arn.split("/")[-1]
            service_arns = ecs.list_services(cluster=cluster_arn).get("serviceArns", [])
            if not service_arns:
                continue

            services = ecs.describe_services(
                cluster=cluster_arn,
                services=service_arns,
            ).get("services", [])

            for svc in services:
                svc_name = svc["serviceName"]
                ecs_node_id = f"ecs_{cluster_name}_{svc_name}"
                if ecs_node_id not in nodes:
                    nodes[ecs_node_id] = _node(ecs_node_id, f"ECS\\n{svc_name[:20]}", "ecs")

                for lb in svc.get("loadBalancers", []):
                    tg_arn = lb.get("targetGroupArn", "")
                    if not tg_arn:
                        continue
                    # Buscar qué ALB tiene este target group
                    try:
                        tgs = elbv2.describe_target_groups(
                            TargetGroupArns=[tg_arn]
                        ).get("TargetGroups", [])
                        for tg in tgs:
                            for lb_arn in tg.get("LoadBalancerArns", []):
                                lb_detail = elbv2.describe_load_balancers(
                                    LoadBalancerArns=[lb_arn]
                                ).get("LoadBalancers", [{}])[0]
                                alb_node_id = f"alb_{lb_detail.get('LoadBalancerName', lb_arn[-8:])}"
                                if alb_node_id in nodes:
                                    edges.append(_edge(alb_node_id, ecs_node_id, "enruta"))
                    except Exception:
                        pass

    except Exception as exc:
        show_aws_error(exc, "ELB/ECS", "obtener conexiones ALB->ECS para grafo")


def _get_ecr_ecs_connections(nodes, edges):
    """ECR -> ECS: imagen usada en cada task definition activa."""
    try:
        ecs = _client("ecs")

        cluster_arns = ecs.list_clusters().get("clusterArns", [])

        for cluster_arn in cluster_arns:
            cluster_name = cluster_arn.split("/")[-1]
            service_arns = ecs.list_services(cluster=cluster_arn).get("serviceArns", [])
            if not service_arns:
                continue

            services = ecs.describe_services(
                cluster=cluster_arn,
                services=service_arns,
            ).get("services", [])

            for svc in services:
                svc_name = svc["serviceName"]
                ecs_node_id = f"ecs_{cluster_name}_{svc_name}"
                if ecs_node_id not in nodes:
                    nodes[ecs_node_id] = _node(ecs_node_id, f"ECS\\n{svc_name[:20]}", "ecs")

                # Obtener imagen de la task definition
                task_def_arn = svc.get("taskDefinition", "")
                if not task_def_arn:
                    continue
                try:
                    containers = ecs.describe_task_definition(
                        taskDefinition=task_def_arn
                    )["taskDefinition"].get("containerDefinitions", [])

                    for container in containers:
                        image = container.get("image", "")
                        # Formato de Imagen ECR: <account>.dkr.ecr.<region>.amazonaws.com/<repo>
                        if "dkr.ecr" in image:
                            repo = image.split("/")[-1].split(":")[0]
                            ecr_node_id = f"ecr_{repo}"
                            if ecr_node_id not in nodes:
                                nodes[ecr_node_id] = _node(ecr_node_id, f"ECR\\n{repo[:20]}", "ecr")
                            edges.append(_edge(ecr_node_id, ecs_node_id, "imagen"))
                except Exception:
                    pass

    except Exception as exc:
        show_aws_error(exc, "ECR/ECS", "obtener conexiones ECR->ECS para grafo")


def _get_ecs_rds_connections(nodes, edges):
    """ECS -> RDS: inferido por security groups compartidos."""
    try:
        ec2 = _client("ec2")
        ecs = _client("ecs")
        rds = _client("rds")

        # Security groups de instancias RDS
        rds_sg_map = {}
        for db in rds.describe_db_instances().get("DBInstances", []):
            db_id = db["DBInstanceIdentifier"]
            rds_node_id = f"rds_{db_id}"
            if rds_node_id not in nodes:
                nodes[rds_node_id] = _node(rds_node_id, f"RDS\\n{db_id[:20]}", "rds")
            for sg in db.get("VpcSecurityGroups", []):
                rds_sg_map[sg["VpcSecurityGroupId"]] = rds_node_id

        if not rds_sg_map:
            return

        # Security groups de tareas ECS en ejecución
        cluster_arns = ecs.list_clusters().get("clusterArns", [])
        for cluster_arn in cluster_arns:
            cluster_name = cluster_arn.split("/")[-1]
            task_arns = ecs.list_tasks(
                cluster=cluster_arn,
                desiredStatus="RUNNING",
            ).get("taskArns", [])
            if not task_arns:
                continue

            tasks = ecs.describe_tasks(
                cluster=cluster_arn,
                tasks=task_arns,
            ).get("tasks", [])

            for task in tasks:
                # Obtener SGs de los attachments de red de la tarea
                for attachment in task.get("attachments", []):
                    for detail in attachment.get("details", []):
                        if detail.get("name") == "networkInterfaceId":
                            eni_id = detail["value"]
                            try:
                                eni = ec2.describe_network_interfaces(
                                    NetworkInterfaceIds=[eni_id]
                                )["NetworkInterfaces"][0]
                                task_sgs = [g["GroupId"] for g in eni.get("Groups", [])]

                                # Buscar el servicio ECS al que pertenece esta tarea
                                svc_name = task.get("group", "").replace("service:", "")
                                ecs_node_id = f"ecs_{cluster_name}_{svc_name}"
                                if ecs_node_id not in nodes:
                                    nodes[ecs_node_id] = _node(
                                        ecs_node_id, f"ECS\\n{svc_name[:20]}", "ecs"
                                    )

                                # Reglas de los SGs de la tarea
                                for sg_id in task_sgs:
                                    sg_detail = ec2.describe_security_groups(
                                        GroupIds=[sg_id]
                                    )["SecurityGroups"][0]
                                    for rule in sg_detail.get("IpPermissionsEgress", []):
                                        for pair in rule.get("UserIdGroupPairs", []):
                                            target_sg = pair.get("GroupId")
                                            if target_sg in rds_sg_map:
                                                rds_node_id = rds_sg_map[target_sg]
                                                edge = _edge(ecs_node_id, rds_node_id, "BD")
                                                if edge not in edges:
                                                    edges.append(edge)
                            except Exception:
                                pass

    except Exception as exc:
        show_aws_error(exc, "ECS/RDS", "obtener conexiones para grafo")


def _get_sns_sqs_connections(nodes, edges):
    """SNS -> SQS: suscripciones con protocolo sqs."""
    try:
        sns = _client("sns")

        topics = sns.list_topics().get("Topics", [])
        for t in topics:
            arn = t["TopicArn"]
            name = arn.split(":")[-1]
            sns_node_id = f"sns_{name}"
            if sns_node_id not in nodes:
                nodes[sns_node_id] = _node(sns_node_id, f"SNS\\n{name[:20]}", "sns")

        subs = sns.list_subscriptions().get("Subscriptions", [])
        for sub in subs:
            if sub.get("Protocol") != "sqs":
                continue

            topic_arn = sub.get("TopicArn", "")
            endpoint = sub.get("Endpoint", "")  # ARN de la cola SQS

            topic_name = topic_arn.split(":")[-1]
            queue_name = endpoint.split(":")[-1]

            sns_node_id = f"sns_{topic_name}"
            sqs_node_id = f"sqs_{queue_name}"

            if sqs_node_id not in nodes:
                nodes[sqs_node_id] = _node(sqs_node_id, f"SQS\\n{queue_name[:20]}", "sqs")

            edges.append(_edge(sns_node_id, sqs_node_id, "publica"))

    except Exception as exc:
        show_aws_error(exc, "SNS/SQS", "obtener suscripciones para grafo")


def _get_remaining_nodes(nodes):
    """Añade nodos de servicios que pueden no tener conexiones detectadas."""
    try:
        # DynamoDB - nodos sin conexiones inferibles
        dynamodb = _client("dynamodb")
        for name in dynamodb.list_tables().get("TableNames", []):
            node_id = f"dynamo_{name}"
            if node_id not in nodes:
                nodes[node_id] = _node(node_id, f"DynamoDB\\n{name[:20]}", "dynamodb")

        # VPC - mostrar VPCs como contexto de red
        ec2 = _client("ec2")
        for vpc in ec2.describe_vpcs().get("Vpcs", []):
            vpc_id = vpc["VpcId"]
            name = next(
                (t["Value"] for t in vpc.get("Tags", []) if t["Key"] == "Name"),
                vpc_id,
            )
            node_id = f"vpc_{vpc_id}"
            if node_id not in nodes:
                nodes[node_id] = _node(node_id, f"VPC\\n{name[:15]}", "vpc")

    except Exception as exc:
        show_aws_error(exc, "DynamoDB/VPC", "obtener nodos adicionales para grafo")


# Función principal
def get_architecture_graph():
    """
    Recopila nodos y conexiones de todos los servicios monitorizados.
    Devuelve (nodes_dict, edges_list) listos para generar el grafo Mermaid.
    """

    if get_mock_mode():
        from mocks.arquitectura_mock import get_architecture_graph
        return get_architecture_graph()

    nodes = {}
    edges = []

    _get_cloudfront_data(nodes, edges)
    _get_alb_ecs_connections(nodes, edges)
    _get_ecr_ecs_connections(nodes, edges)
    _get_ecs_rds_connections(nodes, edges)
    _get_sns_sqs_connections(nodes, edges)
    _get_remaining_nodes(nodes)

    return nodes, edges