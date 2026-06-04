import pandas as pd
from datetime import datetime, timezone

LOG_GROUPS = [
    {"Grupo de Logs": "/ecs/my-api-service",        "Retención (días)": 30,  "Tamaño (MB)": 124.5},
    {"Grupo de Logs": "/ecs/my-worker-service",     "Retención (días)": 14,  "Tamaño (MB)": 45.2},
    {"Grupo de Logs": "/ecs/frontend-service",      "Retención (días)": 7,   "Tamaño (MB)": 12.8},
    {"Grupo de Logs": "/aws/lambda/my-function",    "Retención (días)": 90,  "Tamaño (MB)": 3.1},
    {"Grupo de Logs": "/aws/rds/my-db/error",       "Retención (días)": 365, "Tamaño (MB)": 0.9},
]

LOG_STREAMS = {
    "/ecs/my-api-service": [
        {"Flujo de Logs": "ecs/my-api-service/a1b2c3d4e5f6",  "Último evento": "2025-06-01 14:32:10"},
        {"Flujo de Logs": "ecs/my-api-service/b2c3d4e5f6a1",  "Último evento": "2025-06-01 13:58:44"},
    ],
    "/ecs/my-worker-service": [
        {"Flujo de Logs": "ecs/my-worker-service/c3d4e5f6a1b2", "Último evento": "2025-06-01 14:10:05"},
    ],
    "/ecs/frontend-service": [
        {"Flujo de Logs": "ecs/frontend-service/d4e5f6a1b2c3",  "Último evento": "2025-06-01 09:00:00"},
    ],
    "/aws/lambda/my-function": [
        {"Flujo de Logs": "2025/06/01/[$LATEST]abc123",          "Último evento": "2025-06-01 11:20:33"},
    ],
    "/aws/rds/my-db/error": [
        {"Flujo de Logs": "my-db-instance-1",                   "Último evento": "2025-05-30 08:45:00"},
    ],
}

def _ts(dt_str: str) -> int:
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)

LOG_EVENTS = {
    "ecs/my-api-service/a1b2c3d4e5f6": [
        {"Fecha": _ts("2025-06-01 14:31:00"), "Mensaje": "INFO  Starting application on port 8080"},
        {"Fecha": _ts("2025-06-01 14:31:01"), "Mensaje": "INFO  Connected to database at db.internal:5432"},
        {"Fecha": _ts("2025-06-01 14:31:05"), "Mensaje": "INFO  Health check endpoint registered at /health"},
        {"Fecha": _ts("2025-06-01 14:31:10"), "Mensaje": "INFO  Loaded 42 routes successfully"},
        {"Fecha": _ts("2025-06-01 14:31:15"), "Mensaje": "WARN  Redis connection pool at 80% capacity"},
        {"Fecha": _ts("2025-06-01 14:31:45"), "Mensaje": "INFO  GET /api/v1/users 200 45ms"},
        {"Fecha": _ts("2025-06-01 14:32:00"), "Mensaje": "ERROR Exception in thread 'main' java.lang.NullPointerException"},
        {"Fecha": _ts("2025-06-01 14:32:00"), "Mensaje": "ERROR   at com.myapp.UserService.getUser(UserService.java:87)"},
        {"Fecha": _ts("2025-06-01 14:32:01"), "Mensaje": "ERROR   at com.myapp.UserController.handleRequest(UserController.java:45)"},
        {"Fecha": _ts("2025-06-01 14:32:10"), "Mensaje": "INFO  GET /api/v1/health 200 2ms"},
    ],
    "ecs/my-api-service/b2c3d4e5f6a1": [
        {"Fecha": _ts("2025-06-01 13:55:00"), "Mensaje": "INFO  Container started, task ARN: arn:aws:ecs:eu-west-1:123456789012:task/abc"},
        {"Fecha": _ts("2025-06-01 13:55:10"), "Mensaje": "INFO  Starting application on port 8080"},
        {"Fecha": _ts("2025-06-01 13:56:00"), "Mensaje": "WARN  Slow query detected (1240ms): SELECT * FROM orders WHERE ..."},
        {"Fecha": _ts("2025-06-01 13:58:44"), "Mensaje": "INFO  Graceful shutdown initiated"},
    ],
    "ecs/my-worker-service/c3d4e5f6a1b2": [
        {"Fecha": _ts("2025-06-01 14:00:00"), "Mensaje": "INFO  Worker started, polling queue: sqs://my-jobs-queue"},
        {"Fecha": _ts("2025-06-01 14:05:00"), "Mensaje": "INFO  Processing job job-id-001 (type: email-send)"},
        {"Fecha": _ts("2025-06-01 14:05:03"), "Mensaje": "INFO  Job job-id-001 completed in 3012ms"},
        {"Fecha": _ts("2025-06-01 14:09:00"), "Mensaje": "ERROR Failed to process job job-id-002: SMTP connection refused"},
        {"Fecha": _ts("2025-06-01 14:09:01"), "Mensaje": "WARN  Retrying job job-id-002 (attempt 1/3)"},
        {"Fecha": _ts("2025-06-01 14:10:05"), "Mensaje": "INFO  Job job-id-002 completed on retry"},
    ],
    "ecs/frontend-service/d4e5f6a1b2c3": [
        {"Fecha": _ts("2025-06-01 09:00:00"), "Mensaje": "INFO  Nginx started, listening on 0.0.0.0:80"},
        {"Fecha": _ts("2025-06-01 09:00:01"), "Mensaje": "INFO  Static assets loaded from /app/dist"},
    ],
    "2025/06/01/[$LATEST]abc123": [
        {"Fecha": _ts("2025-06-01 11:20:30"), "Mensaje": "START RequestId: abc-123 Version: $LATEST"},
        {"Fecha": _ts("2025-06-01 11:20:32"), "Mensaje": "INFO  Processing S3 event for bucket: my-bucket"},
        {"Fecha": _ts("2025-06-01 11:20:33"), "Mensaje": "END RequestId: abc-123"},
    ],
    "my-db-instance-1": [
        {"Fecha": _ts("2025-05-30 08:45:00"), "Mensaje": "ERROR  could not connect to the primary server: connection refused"},
    ],
}


def get_log_groups_dataframe(prefix_filter: str = "") -> pd.DataFrame:
    groups = LOG_GROUPS
    if prefix_filter:
        groups = [g for g in groups if g["Grupo de Logs"].startswith(prefix_filter)]
    return pd.DataFrame(groups)


def get_log_streams_dataframe(log_group: str) -> pd.DataFrame:
    streams = LOG_STREAMS.get(log_group, [])
    return pd.DataFrame(streams)


def get_log_events_dataframe(log_group: str, log_stream: str, limit: int = 100) -> pd.DataFrame:
    events = LOG_EVENTS.get(log_stream, [])[-limit:]
    return pd.DataFrame(events)