import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timezone
from config import get_mock_mode


from aws.ecr import (
    describe_repositories,
    describe_images,
    describe_image_scan_findings,
    get_lifecycle_policy,
    get_repository_policy,
    list_tags_for_resource
)
from utils.tag_filter import get_tag_filter

st.set_page_config(
    page_title="ECR",
    layout="wide"
)

st.title("Elastic Container Registry (ECR)")

def ensure_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_datetime_columns_for_table(dataframe, columns):
    """Convierte columnas datetime a UTC sin zona para evitar fallos de pyarrow/dateutil."""

    for column in columns:
        if column in dataframe.columns:
            dataframe[column] = pd.to_datetime(
                dataframe[column],
                errors="coerce",
                utc=True
            ).dt.tz_localize(None)

    return dataframe


def formato_es(numero):
    if numero is None:
        return None
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data(ttl=300)
def build_repository_dataframe(mock_mode_enabled):

    # mock_mode_enabled solo se usa para invalidar cache al cambiar de real a mock (o al reves)
    _ = mock_mode_enabled

    repos = describe_repositories()
    rows = []
    now = datetime.now(timezone.utc)

    for repo in repos:

        name = repo["repositoryName"]
        uri = repo["repositoryUri"]
        arn = repo["repositoryArn"]

        created = ensure_utc(repo["createdAt"])

        scan_on_push = repo.get("imageScanningConfiguration", {}).get("scanOnPush")
        tag_mutability = repo.get("imageTagMutability")
        encryption = repo.get("encryptionConfiguration", {}).get("encryptionType")

        repo_tags = list_tags_for_resource(arn)
        lifecycle = get_lifecycle_policy(name)
        policy = get_repository_policy(name)

        images = describe_images(name)

        image_count = len(images)
        total_size = 0
        max_size = 0

        untagged = 0
        tag_count = 0

        latest_push = None
        first_push = None

        vuln_critical = 0
        vuln_high = 0
        vuln_medium = 0
        vuln_low = 0

        for img in images:

            size = img.get("imageSizeInBytes", 0)
            total_size += size

            if size > max_size:
                max_size = size

            tags = img.get("imageTags")
            if tags:
                tag_count += len(tags)
            else:
                untagged += 1

            pushed = ensure_utc(img.get("imagePushedAt"))

            if pushed:
                if latest_push is None or pushed > latest_push:
                    latest_push = pushed
                if first_push is None or pushed < first_push:
                    first_push = pushed

            scan_summary = img.get("imageScanFindingsSummary")

            # En mock mode y en algunos repos reales, el resumen no viene en describe_images.
            if not scan_summary and img.get("imageDigest"):
                findings = describe_image_scan_findings(name, img.get("imageDigest"))
                scan_summary = findings.get("imageScanFindings", {})

            if scan_summary:
                counts = scan_summary.get("findingSeverityCounts", {})
                vuln_critical += counts.get("CRITICAL", 0)
                vuln_high += counts.get("HIGH", 0)
                vuln_medium += counts.get("MEDIUM", 0)
                vuln_low += counts.get("LOW", 0)

        avg_size = total_size / image_count if image_count else 0

        days_since_push = None
        if latest_push:
            days_since_push = (now - latest_push).days

        rows.append({
            "Repositorio": name,
            "URI": uri,
            "Creado": created,
            "Número de imágenes": image_count,
            "Etiquetas totales": tag_count,
            "Imágenes sin etiqueta": untagged,
            "Tamaño total (MB)": round(total_size / (1024 * 1024), 2),
            "Tamaño medio (MB)": round(avg_size / (1024 * 1024), 2),
            "Tamaño máximo (MB)": round(max_size / (1024 * 1024), 2),
            "Primera subida": first_push,
            "Última subida": latest_push,
            "Días desde última subida": days_since_push,
            "Escaneo al subir": scan_on_push,
            "Mutabilidad de tags": tag_mutability,
            "Cifrado": encryption,
            "Política de ciclo de vida": lifecycle is not None,
            "Política de repositorio": policy is not None,
            "Tags del repositorio": len(repo_tags),
            "Vulnerabilidades BAJAS": vuln_low,
            "Vulnerabilidades MEDIAS": vuln_medium,
            "Vulnerabilidades ALTAS": vuln_high,
            "Vulnerabilidades CRÍTICAS": vuln_critical
        })

    df = pd.DataFrame(rows)

    return normalize_datetime_columns_for_table(
        df,
        ["Creado", "Primera subida", "Última subida"]
    )


df = build_repository_dataframe(get_mock_mode())

if df.empty:
    tag_filter = get_tag_filter()
    if tag_filter:
        all_repos = describe_repositories(apply_tag_filter=False)
        if all_repos:
            st.info(
                f"No se encontraron repositorios ECR con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
        else:
            st.info("No se encontraron repositorios ECR para monitorizar.")
    else:
        st.info("No se encontraron repositorios ECR para monitorizar.")
    st.stop()

repo_list = df["Repositorio"].tolist() if not df.empty else []

selected_repos = st.multiselect(
    "Selecciona repositorios",
    options=repo_list,
    default=repo_list,
    help="Selecciona uno o varios repositorios para analizar su estado. Si no seleccionas ninguno, no se mostrará información.",
    placeholder="Selecciona repositorios... (puedes seleccionar varios)"
)

if selected_repos:
    filtered_df = df[df["Repositorio"].isin(selected_repos)]
else:
    filtered_df = df.iloc[0:0]

single_repo = len(selected_repos) == 1

st.subheader("Estado de los repositorios")

st.dataframe(
    filtered_df,
    width='stretch',
    hide_index=True
)

if not filtered_df.empty:

    st.subheader("Resumen general")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Imágenes totales",
        int(filtered_df["Número de imágenes"].sum())
    )

    col2.metric(
        "Tamaño total (MB)",
        formato_es(filtered_df["Tamaño total (MB)"].sum())
    )

    col3.metric(
        "Vulnerabilidades críticas",
        int(filtered_df["Vulnerabilidades CRÍTICAS"].sum())
    )

    if not single_repo:

        st.subheader("Imágenes por repositorio")
        st.bar_chart(
            filtered_df.set_index("Repositorio")["Número de imágenes"],
            width='stretch'
        )

        st.subheader("Uso de almacenamiento (MB)")
        st.bar_chart(
            filtered_df.set_index("Repositorio")["Tamaño total (MB)"],
            width='stretch'
        )

    st.subheader("Vulnerabilidades de seguridad")

    severity_order = [
        "Vulnerabilidades BAJAS",
        "Vulnerabilidades MEDIAS",
        "Vulnerabilidades ALTAS",
        "Vulnerabilidades CRÍTICAS",
    ]

    vuln_by_repo = filtered_df[["Repositorio"] + severity_order].melt(
        id_vars=["Repositorio"],
        value_vars=severity_order,
        var_name="Severidad",
        value_name="Total",
    )

    vuln_chart = alt.Chart(vuln_by_repo).mark_bar().encode(
        x=alt.X("Repositorio:N", title="Repositorio"),
        xOffset=alt.XOffset("Severidad:N", sort=severity_order),
        y=alt.Y("Total:Q", title="Total"),
        color=alt.Color("Severidad:N", sort=severity_order, title="Severidad"),
        tooltip=["Repositorio", "Severidad", "Total"],
    )

    st.altair_chart(vuln_chart, width='stretch')
