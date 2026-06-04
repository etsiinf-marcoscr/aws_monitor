import streamlit as st


# Clave usada en st.session_state para persistir el filtro entre páginas
_SESSION_KEY = "active_tag_filter"


def set_tag_filter(key: str, value: str) -> None:
    """Guarda el filtro activo en session_state. Llamado desde el sidebar."""
    if key.strip() and value.strip():
        st.session_state[_SESSION_KEY] = {"key": key.strip(), "value": value.strip()}
    else:
        st.session_state[_SESSION_KEY] = None


def clear_tag_filter() -> None:
    """Elimina el filtro activo."""
    st.session_state[_SESSION_KEY] = None


def get_tag_filter() -> dict | None:
    """
    Devuelve el filtro activo como {'key': ..., 'value': ...} o None si no hay filtro.
    Es la función que llaman los módulos /aws para saber si deben filtrar.
    """
    return st.session_state.get(_SESSION_KEY, None)


def apply_tag_filter_to_list(resources: list[dict], tag_filter: dict | None) -> list[dict]:
    """
    Filtra una lista de recursos por tag en el lado cliente (post-filtrado).
    Útil para servicios cuya API no soporta filtrado nativo por tags (CloudFront, S3...).

    Espera que cada recurso tenga una clave 'tags' con formato lista de dicts:
        [{"Key": "stack", "Value": "arquitectura1"}, ...]
    o formato dict plano:
        {"stack": "arquitectura1", ...}
    """
    if tag_filter is None:
        return resources

    key   = tag_filter["key"]
    value = tag_filter["value"]

    filtered = []
    for resource in resources:
        tags = resource.get("tags", [])

        # Formato lista de dicts [{"Key": ..., "Value": ...}]
        if isinstance(tags, list):
            match = any(
                t.get("Key") == key and t.get("Value") == value
                for t in tags
            )
        # Formato dict plano {"key": "value"}
        elif isinstance(tags, dict):
            match = tags.get(key) == value
        else:
            match = False

        if match:
            filtered.append(resource)

    return filtered


def is_filter_active() -> bool:
    """Devuelve True si hay un filtro activo en este momento."""
    return get_tag_filter() is not None