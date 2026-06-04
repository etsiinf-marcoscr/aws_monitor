import pandas as pd
from datetime import datetime, timedelta


def get_user_pools_dataframe():

    now = datetime.utcnow()

    rows = [
        {"Grupo de Usuarios": "my-app-pool", "ID": "us-east-1_Abc123", "Creado": now - timedelta(days=400)},
        {"Grupo de Usuarios": "internal-admins", "ID": "us-east-1_Xyz789", "Creado": now - timedelta(days=200)}
    ]

    dataframe = pd.DataFrame(rows)
    dataframe["Creado"] = pd.to_datetime(
        dataframe["Creado"],
        utc=True,
        errors="coerce",
    ).dt.tz_localize(None)

    return dataframe


def get_user_pool_clients_dataframe(pool_id):

    rows = []

    if pool_id.endswith("Abc123"):
        rows = [
            {"Nombre del Cliente": "web-client", "ID del Cliente": "1abc234def"},
            {"Nombre del Cliente": "mobile-client", "ID del Cliente": "2ghi567jkl"}
        ]
    else:
        rows = [
            {"Nombre del Cliente": "admin-console", "ID del Cliente": "3mno890pqr"}
        ]

    return pd.DataFrame(rows)


def get_users_dataframe(pool_id):

    now = datetime.utcnow()

    if pool_id.endswith("Abc123"):
        users = [
            {
                "Nombre de Usuario": "alice",
                "Estado": "CONFIRMED",
                "Habilitado": True,
                "Fecha creación": now - timedelta(days=300),
                "Última modificación": now - timedelta(days=5),
                "Correo Electrónico": "alice@example.com"
            },
            {
                "Nombre de Usuario": "bob",
                "Estado": "UNCONFIRMED",
                "Habilitado": False,
                "Fecha creación": now - timedelta(days=10),
                "Última modificación": now - timedelta(days=9),
                "Correo Electrónico": "bob@example.com"
            }
        ]
    else:
        users = [
            {
                "Nombre de Usuario": "admin",
                "Estado": "CONFIRMED",
                "Habilitado": True,
                "Fecha creación": now - timedelta(days=250),
                "Última modificación": now - timedelta(days=1),
                "Correo Electrónico": "admin@example.com"
            }
        ]

    dataframe = pd.DataFrame(users)

    for column in ("Fecha creación", "Última modificación"):
        dataframe[column] = pd.to_datetime(
            dataframe[column],
            utc=True,
            errors="coerce",
        ).dt.tz_localize(None)

    return dataframe


def get_user_counts(pool_id):
    df = get_users_dataframe(pool_id)

    total = len(df)
    confirmed = int((df["Estado"] == "CONFIRMED").sum()) if not df.empty else 0
    unconfirmed = total - confirmed
    enabled = int((df["Habilitado"] == True).sum()) if not df.empty else 0

    return {
        "total": total,
        "confirmed": confirmed,
        "unconfirmed": unconfirmed,
        "enabled": enabled,
        "disabled": total - enabled
    }


def get_sign_in_metrics(pool_id):
    import random
    from datetime import datetime, timedelta

    now = datetime.utcnow()

    rows = []

    for i in range(60):
        rows.append({
            "instante": now - timedelta(minutes=59 - i),
            "Inicios de Sesión": random.randint(0, 20)
        })

    return pd.DataFrame(rows)


def get_sign_up_metrics(pool_id):
    import random
    from datetime import datetime, timedelta

    now = datetime.utcnow()

    rows = []

    for i in range(60):
        rows.append({
            "instante": now - timedelta(minutes=59 - i),
            "Registros": random.randint(0, 5)
        })

    return pd.DataFrame(rows)
