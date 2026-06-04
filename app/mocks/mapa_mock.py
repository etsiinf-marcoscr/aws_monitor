# Coordenadas de las regiones AWS más comunes
REGION_COORDS = {
    "us-east-1":      {"lat": 38.13,  "lon": -78.45,  "label": "US East (N. Virginia)"},
    "us-east-2":      {"lat": 39.96,  "lon": -83.00,  "label": "US East (Ohio)"},
    "us-west-1":      {"lat": 37.77,  "lon": -122.41, "label": "US West (N. California)"},
    "us-west-2":      {"lat": 45.52,  "lon": -122.67, "label": "US West (Oregon)"},
    "eu-west-1":      {"lat": 53.33,  "lon": -6.25,   "label": "Europe (Ireland)"},
    "eu-west-2":      {"lat": 51.50,  "lon": -0.12,   "label": "Europe (London)"},
    "eu-west-3":      {"lat": 48.85,  "lon": 2.35,    "label": "Europe (Paris)"},
    "eu-central-1":   {"lat": 50.11,  "lon": 8.68,    "label": "Europe (Frankfurt)"},
    "eu-north-1":     {"lat": 59.33,  "lon": 18.06,   "label": "Europe (Stockholm)"},
    "ap-southeast-1": {"lat": 1.35,   "lon": 103.82,  "label": "Asia Pacific (Singapore)"},
    "ap-southeast-2": {"lat": -33.86, "lon": 151.20,  "label": "Asia Pacific (Sydney)"},
    "ap-northeast-1": {"lat": 35.68,  "lon": 139.69,  "label": "Asia Pacific (Tokyo)"},
    "ap-south-1":     {"lat": 19.08,  "lon": 72.88,   "label": "Asia Pacific (Mumbai)"},
    "sa-east-1":      {"lat": -23.55, "lon": -46.63,  "label": "South America (São Paulo)"},
    "ca-central-1":   {"lat": 45.50,  "lon": -73.56,  "label": "Canada (Central)"},
}

# Coordenadas de edge locations de CloudFront (algunas)
CLOUDFRONT_EDGE_LOCATIONS = [
    {"city": "Madrid",       "lat": 40.41,  "lon": -3.70},
    {"city": "Frankfurt",    "lat": 50.11,  "lon": 8.68},
    {"city": "Londres",      "lat": 51.50,  "lon": -0.12},
    {"city": "París",        "lat": 48.85,  "lon": 2.35},
    {"city": "Ámsterdam",    "lat": 52.37,  "lon": 4.90},
    {"city": "Estocolmo",    "lat": 59.33,  "lon": 18.06},
    {"city": "Dublín",       "lat": 53.33,  "lon": -6.25},
    {"city": "Nueva York",   "lat": 40.71,  "lon": -74.00},
    {"city": "Virginia",     "lat": 38.13,  "lon": -78.45},
    {"city": "Chicago",      "lat": 41.88,  "lon": -87.63},
    {"city": "Dallas",       "lat": 32.78,  "lon": -96.80},
    {"city": "Los Ángeles",  "lat": 34.05,  "lon": -118.24},
    {"city": "São Paulo",    "lat": -23.55, "lon": -46.63},
    {"city": "Tokio",        "lat": 35.68,  "lon": 139.69},
    {"city": "Singapur",     "lat": 1.35,   "lon": 103.82},
    {"city": "Sídney",       "lat": -33.86, "lon": 151.20},
    {"city": "Mumbai",       "lat": 19.08,  "lon": 72.88},
    {"city": "Seúl",         "lat": 37.57,  "lon": 126.98},
    {"city": "Johannesburgo","lat": -26.20, "lon": 28.04},
    {"city": "Dubái",        "lat": 25.20,  "lon": 55.27},
]

# Tareas ECS simuladas distribuidas por varias regiones
MOCK_ECS_TASKS = [
    # Irlanda
    {"task_id": "task-001", "cluster": "prod-cluster",    "service": "api-gateway",    "region": "eu-west-1", "az": "eu-west-1a", "status": "RUNNING", "cpu": "512",  "memory": "1024"},
    {"task_id": "task-002", "cluster": "prod-cluster",    "service": "api-gateway",    "region": "eu-west-1", "az": "eu-west-1b", "status": "RUNNING", "cpu": "512",  "memory": "1024"},
    {"task_id": "task-003", "cluster": "prod-cluster",    "service": "auth-service",   "region": "eu-west-1", "az": "eu-west-1a", "status": "RUNNING", "cpu": "256",  "memory": "512"},
    {"task_id": "task-004", "cluster": "prod-cluster",    "service": "worker",         "region": "eu-west-1", "az": "eu-west-1c", "status": "STOPPED", "cpu": "256",  "memory": "512"},
    {"task_id": "task-005", "cluster": "staging-cluster", "service": "api-gateway",    "region": "eu-west-1", "az": "eu-west-1a", "status": "RUNNING", "cpu": "256",  "memory": "512"},
    # Frankfurt
    {"task_id": "task-006", "cluster": "prod-cluster",    "service": "api-gateway",    "region": "eu-central-1", "az": "eu-central-1a", "status": "RUNNING", "cpu": "512",  "memory": "1024"},
    {"task_id": "task-007", "cluster": "prod-cluster",    "service": "notification-svc","region": "eu-central-1","az": "eu-central-1b", "status": "RUNNING", "cpu": "256",  "memory": "512"},
    # Virginia
    {"task_id": "task-008", "cluster": "prod-cluster",    "service": "api-gateway",    "region": "us-east-1", "az": "us-east-1a", "status": "RUNNING", "cpu": "1024", "memory": "2048"},
    {"task_id": "task-009", "cluster": "prod-cluster",    "service": "api-gateway",    "region": "us-east-1", "az": "us-east-1b", "status": "RUNNING", "cpu": "1024", "memory": "2048"},
    {"task_id": "task-010", "cluster": "prod-cluster",    "service": "worker",         "region": "us-east-1", "az": "us-east-1a", "status": "STOPPED", "cpu": "512",  "memory": "1024"},
    # Tokio
    {"task_id": "task-011", "cluster": "prod-cluster",    "service": "api-gateway",    "region": "ap-northeast-1", "az": "ap-northeast-1a", "status": "RUNNING", "cpu": "512", "memory": "1024"},
    # São Paulo
    {"task_id": "task-012", "cluster": "prod-cluster",    "service": "api-gateway",    "region": "sa-east-1", "az": "sa-east-1a", "status": "RUNNING", "cpu": "256", "memory": "512"},
]


def get_ecs_tasks_for_map():
    return MOCK_ECS_TASKS


def get_cloudfront_edges_for_map():
    return CLOUDFRONT_EDGE_LOCATIONS


def get_region_coords():
    return REGION_COORDS


def get_service_nodes_for_map():
    return [
        {"service": "ECS Tasks", "region": "eu-west-1", "region_label": "Europe (Ireland)", "count": 5, "lat": 53.33, "lon": -6.25, "color_key": "ecs"},
        {"service": "RDS Instances", "region": "eu-west-1", "region_label": "Europe (Ireland)", "count": 2, "lat": 53.33, "lon": -6.25, "color_key": "rds"},
        {"service": "DynamoDB Tables", "region": "eu-central-1", "region_label": "Europe (Frankfurt)", "count": 4, "lat": 50.11, "lon": 8.68, "color_key": "dynamodb"},
        {"service": "S3 Buckets", "region": "us-east-1", "region_label": "US East (N. Virginia)", "count": 3, "lat": 38.13, "lon": -78.45, "color_key": "s3"},
        {"service": "SQS Queues", "region": "us-east-1", "region_label": "US East (N. Virginia)", "count": 6, "lat": 38.13, "lon": -78.45, "color_key": "sqs"},
        {"service": "SNS Topics", "region": "ap-northeast-1", "region_label": "Asia Pacific (Tokyo)", "count": 3, "lat": 35.68, "lon": 139.69, "color_key": "sns"},
        {"service": "Cognito Pools", "region": "eu-west-2", "region_label": "Europe (London)", "count": 1, "lat": 51.50, "lon": -0.12, "color_key": "cognito"},
    ]
