from config import get_mock_mode
from utils.aws_errors import is_aws_error_code, show_aws_error
from utils.aws_session import get_session
from utils.tag_filter import get_tag_filter, apply_tag_filter_to_list

import pandas as pd


def get_ecr_client():
    """Crea cliente ECR cuando la app no esta en modo mock."""

    if get_mock_mode():
        return None

    try:
        return get_session().client("ecr")
    except Exception as exc:
        show_aws_error(exc, "ECR", "crear cliente")
        return None


def describe_repositories(apply_tag_filter: bool = True):
    """
    Devuelve todos los repositorios ECR de la cuenta actual.
    Si hay un filtro de tag activo, enriquece cada repositorio con sus tags
    y filtra antes de devolver - ECR no soporta filtrado nativo por tag en la API.
    """

    if get_mock_mode():
        from mocks.ecr_mock import describe_repositories
        return describe_repositories()

    try:
        ecr = get_ecr_client()

        if ecr is None:
            return []

        repos = ecr.describe_repositories().get("repositories", [])
        tag_filter = get_tag_filter() if apply_tag_filter else None

        if tag_filter is None:
            return repos

        # hay que obtener las tags de cada repositorio por separado
        for repo in repos:
            raw_tags = ecr.list_tags_for_resource(
                resourceArn=repo["repositoryArn"]
            ).get("tags", [])
            # Tags de ECR vienen como [{"Key": ..., "Value": ...}]
            repo["tags"] = raw_tags

        return apply_tag_filter_to_list(repos, tag_filter)

    except Exception as exc:
        show_aws_error(exc, "ECR", "obtener repositorios")
        return []


def describe_images(repository_name):
    """Lista imagenes de un repositorio ECR manejando paginacion."""

    if get_mock_mode():
        from mocks.ecr_mock import describe_images
        return describe_images(repository_name)

    try:
        ecr = get_ecr_client()

        if ecr is None:
            return []

        images = []
        next_token = None

        while True:
            params = {"repositoryName": repository_name}

            if next_token:
                params["nextToken"] = next_token

            response = ecr.describe_images(**params)
            images.extend(response.get("imageDetails", []))
            next_token = response.get("nextToken")

            if not next_token:
                break

        return images
    except Exception as exc:
        show_aws_error(exc, "ECR", f"obtener imagenes de {repository_name}")
        return []


def describe_image_scan_findings(repository_name, image_digest):
    """Obtiene el detalle de findings de escaneo para una imagen concreta."""

    if get_mock_mode():
        from mocks.ecr_mock import describe_image_scan_findings
        return describe_image_scan_findings(repository_name, image_digest)

    try:
        ecr = get_ecr_client()

        if ecr is None:
            return {}

        return ecr.describe_image_scan_findings(
            repositoryName=repository_name,
            imageId={"imageDigest": image_digest},
        )
    except Exception as exc:
        if is_aws_error_code(exc, ["ScanNotFoundException", "ImageNotFoundException"]):
            return {}

        show_aws_error(exc, "ECR", f"obtener findings de escaneo para {repository_name}")
        return {}


def get_lifecycle_policy(repository_name):
    """Obtiene la politica de ciclo de vida del repositorio si existe."""

    if get_mock_mode():
        from mocks.ecr_mock import get_lifecycle_policy
        return get_lifecycle_policy(repository_name)

    try:
        ecr = get_ecr_client()

        if ecr is None:
            return None

        return ecr.get_lifecycle_policy(repositoryName=repository_name)
    except Exception as exc:
        if is_aws_error_code(exc, "LifecyclePolicyNotFoundException"):
            return None

        show_aws_error(exc, "ECR", f"obtener lifecycle policy de {repository_name}")
        return None


def get_repository_policy(repository_name):
    """Obtiene la politica de acceso del repositorio si existe."""

    if get_mock_mode():
        from mocks.ecr_mock import get_repository_policy
        return get_repository_policy(repository_name)

    try:
        ecr = get_ecr_client()

        if ecr is None:
            return None

        return ecr.get_repository_policy(repositoryName=repository_name)
    except Exception as exc:
        if is_aws_error_code(exc, "RepositoryPolicyNotFoundException"):
            return None

        show_aws_error(exc, "ECR", f"obtener repository policy de {repository_name}")
        return None


def list_tags_for_resource(repository_arn):
    """Devuelve tags asociados a un recurso ECR por ARN."""

    if get_mock_mode():
        from mocks.ecr_mock import list_tags_for_resource
        return list_tags_for_resource(repository_arn)

    try:
        ecr = get_ecr_client()

        if ecr is None:
            return []

        return ecr.list_tags_for_resource(
            resourceArn=repository_arn
        ).get("tags", [])
    except Exception as exc:
        show_aws_error(exc, "ECR", "obtener tags del repositorio")
        return []


def normalize_datetime_columns_for_table(dataframe, columns):
    """Convierte columnas datetime a UTC sin zona para evitar fallos de serializacion."""

    for column in columns:
        if column in dataframe.columns:
            dataframe[column] = pd.to_datetime(
                dataframe[column],
                errors="coerce",
                utc=True,
            ).dt.tz_localize(None)

    return dataframe


def get_repositories_dataframe(apply_tag_filter: bool = True):
    """Transforma la descripcion de repositorios ECR en un DataFrame amigable."""

    try:
        repos = describe_repositories(apply_tag_filter=apply_tag_filter)
        rows = []

        for repo in repos:
            rows.append({
                "Repositorio": repo.get("repositoryName"),
                "URI": repo.get("repositoryUri"),
                "Creado": repo.get("createdAt"),
                "Mutabilidad": repo.get("imageTagMutability"),
                "Escaneo al subir": repo.get(
                    "imageScanningConfiguration", {}
                ).get("scanOnPush", False),
                "Cifrado": repo.get(
                    "encryptionConfiguration", {}
                ).get("encryptionType"),
            })

        df = pd.DataFrame(rows)

        return normalize_datetime_columns_for_table(df, ["Creado"])
    except Exception as exc:
        show_aws_error(exc, "ECR", "construir tabla de repositorios")
        return pd.DataFrame()
