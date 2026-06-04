import random
import pandas as pd
from datetime import datetime, timedelta


def get_rds_instances_dataframe():

    engines = ["postgres", "mysql", "mariadb"]

    rows = []

    for i in range(3):
        rows.append({
            "ID Base de Datos": f"database-{i}",
            "Motor": random.choice(engines),
            "Estado": "available",
            "Procesador": "db.t3.micro",
            "Almacenamiento (GB)": random.choice([20, 50, 100]),
            "Multi-AZ": random.choice([True, False]),
            "Periodo de Backup": random.randint(1, 7),
            "Endpoint": f"db-{i}.abcd.eu-west-1.rds.amazonaws.com"
        })

    return pd.DataFrame(rows)


def _generate_timeseries(field_name):

    now = datetime.utcnow()
    rows = []

    base = random.randint(20, 80)

    for i in range(30):
        rows.append({
            "instante": now - timedelta(minutes=30 - i),
            field_name: base + random.randint(-10, 10)
        })

    return pd.DataFrame(rows)


def get_rds_cpu_metrics(db_identifier):
    return _generate_timeseries("cpu")


def get_rds_free_storage_metrics(db_identifier):
    return _generate_timeseries("espacio libre")


def get_rds_connections_metrics(db_identifier):
    return _generate_timeseries("conexiones")


def get_rds_read_iops_metrics(db_identifier):
    return _generate_timeseries("read_iops")


def get_rds_write_iops_metrics(db_identifier):
    return _generate_timeseries("write_iops")


def get_rds_events(db_identifier):

    events = []

    for i in range(5):
        events.append({
            "Instante": datetime.utcnow() - timedelta(minutes=i * 10),
            "Descripción del evento": random.choice([
                "Backup completed successfully",
                "DB instance restarted",
                "Maintenance window executed",
                "Storage autoscaling triggered"
            ])
        })

    return pd.DataFrame(events)


def get_rds_snapshots(db_identifier):

    snapshots = []

    for i in range(3):
        snapshots.append({
            "Snapshot": f"snapshot-{db_identifier}-{i}",
            "Estado": "available",
            "Fecha de creación": datetime.utcnow() - timedelta(days=i),
            "Tamaño (GB)": random.choice([20, 50, 100])
        })

    return pd.DataFrame(snapshots)