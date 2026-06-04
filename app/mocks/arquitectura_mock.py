def _node(id, label, tipo):
    return {"id": id, "label": label, "tipo": tipo}


def _edge(source, target, label=""):
    return {"source": source, "target": target, "label": label}


def get_architecture_graph():
    nodes = {
        # Red
        "vpc_main":          _node("vpc_main",          "VPC\\nprod-vpc",          "vpc"),
        # CDN y seguridad
        "waf_main":          _node("waf_main",           "WAF\\nprod-waf",          "waf"),
        "cf_main":           _node("cf_main",            "CloudFront\\nprod-cdn",   "cloudfront"),
        # Balanceador
        "alb_main":          _node("alb_main",           "ALB\\nprod-alb",          "alb"),
        # Almacenamiento estático
        "s3_assets":         _node("s3_assets",          "S3\\nprod-assets",        "s3"),
        # Contenedores
        "ecr_api":           _node("ecr_api",            "ECR\\napi-service",       "ecr"),
        "ecr_worker":        _node("ecr_worker",         "ECR\\nworker-service",    "ecr"),
        "ecs_api":           _node("ecs_api",            "ECS\\napi-service",       "ecs"),
        "ecs_worker":        _node("ecs_worker",         "ECS\\nworker-service",    "ecs"),
        # Bases de datos
        "rds_main":          _node("rds_main",           "RDS\\nprod-aurora",       "rds"),
        "dynamo_sessions":   _node("dynamo_sessions",    "DynamoDB\\nsessions",     "dynamodb"),
        "dynamo_events":     _node("dynamo_events",      "DynamoDB\\nevents",       "dynamodb"),
        # Mensajería
        "sns_events":        _node("sns_events",         "SNS\\nevents-topic",      "sns"),
        "sqs_worker":        _node("sqs_worker",         "SQS\\nworker-queue",      "sqs"),
        "sqs_dlq":           _node("sqs_dlq",            "SQS\\nworker-dlq",        "sqs"),
    }

    edges = [
        # Seguridad y CDN
        _edge("waf_main",       "cf_main",       "protege"),
        _edge("cf_main",        "s3_assets",     "origen"),
        _edge("cf_main",        "alb_main",      "origen"),
        # Balanceador -> contenedores
        _edge("alb_main",       "ecs_api",       "enruta"),
        # Imágenes ECR
        _edge("ecr_api",        "ecs_api",       "imagen"),
        _edge("ecr_worker",     "ecs_worker",    "imagen"),
        # Contenedores -> bases de datos
        _edge("ecs_api",        "rds_main",      "BD"),
        _edge("ecs_api",        "dynamo_sessions","BD"),
        _edge("ecs_worker",     "dynamo_events", "BD"),
        # Mensajería
        _edge("ecs_api",        "sns_events",    "publica"),
        _edge("sns_events",     "sqs_worker",    "publica"),
        _edge("ecs_worker",     "sqs_worker",    "consume"),
        _edge("sqs_worker",     "sqs_dlq",       "DLQ"),
    ]

    return nodes, edges