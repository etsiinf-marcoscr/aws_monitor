import streamlit as st
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, PartialCredentialsError


def _extract_client_error_code(exc):
    """Extrae el codigo de error de ClientError cuando existe."""
    if isinstance(exc, ClientError):
        return exc.response.get("Error", {}).get("Code")

    return None


def is_aws_error_code(exc, expected_codes):
    """Comprueba si una excepcion AWS coincide con alguno de los codigos esperados."""
    if isinstance(expected_codes, str):
        expected_codes = {expected_codes}
    else:
        expected_codes = set(expected_codes)

    return _extract_client_error_code(exc) in expected_codes


def build_friendly_aws_error_message(exc, service_name, action):
    """Genera un mensaje legible para el frontend a partir de errores AWS comunes."""
    if isinstance(exc, (NoCredentialsError, PartialCredentialsError)):
        return (
            f"No se pudieron usar credenciales AWS para {service_name}. "
            "Revisa Access Key, Secret Key y Session Token en el panel lateral o en el archivo .env."
        )

    if isinstance(exc, ClientError):
        code = _extract_client_error_code(exc)

        if code in {
            "AccessDenied",
            "AccessDeniedException",
            "UnauthorizedOperation",
            "UnauthorizedException",
            "Client.UnauthorizedOperation",
        }:
            return (
                f"No tienes permisos suficientes para {action} en {service_name}. "
                "Pide acceso de lectura al servicio o usa un perfil con permisos adecuados."
            )

        if code in {"UnrecognizedClientException", "InvalidClientTokenId", "SignatureDoesNotMatch"}:
            return (
                f"Las credenciales AWS no son validas para {service_name}. "
                "Verifica las claves configuradas y que pertenezcan a la cuenta correcta."
            )

        if code in {"ExpiredToken", "RequestExpired"}:
            return (
                f"La sesion AWS ha expirado al intentar {action} en {service_name}. "
                "Actualiza el token temporal o inicia sesion de nuevo."
            )

        return (
            f"No se pudo {action} en {service_name}. "
            f"AWS devolvio el error {code}."
        )

    if isinstance(exc, BotoCoreError):
        return (
            f"Error de comunicacion con AWS al intentar {action} en {service_name}. "
            "Revisa conectividad de red y configuracion regional."
        )

    return f"Error inesperado al intentar {action} en {service_name}."


def show_aws_error(exc, service_name, action):
    """Muestra en Streamlit un error AWS en formato entendible para usuario final."""
    st.error(build_friendly_aws_error_message(exc, service_name, action))
