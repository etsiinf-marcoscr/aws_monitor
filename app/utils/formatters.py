def bytes_to_mb(value):
    """Convierte bytes a MB con dos decimales para mostrar en tablas/graficos."""
    if value is None:
        return 0

    return round(value / (1024 * 1024), 2)


def format_datetime(value):
    """Formatea datetime a una cadena corta y legible para la interfaz."""
    if value is None:
        return ""

    return value.strftime("%Y-%m-%d %H:%M")