import streamlit as st
from datetime import datetime, timezone

from config import get_mock_mode
from utils.tag_filter import get_tag_filter, is_filter_active
from utils.informe_builder import SECTIONS, build_report

st.set_page_config(page_title="Informe AWS", page_icon="📄", layout="wide")

st.title("Generador de informe AWS")

st.markdown(
    "<small>Genera un informe Markdown con el estado actual de la infraestructura AWS de la cuenta asociada.<br>"
    "Por favor tenga en cuenta que la velocidad de generación variará en función de la cantidad de recursos y secciones seleccionadas, así como de la latencia de las APIs de AWS. En cuentas con muchos recursos, la generación puede tardar varios minutos.</small>",
    unsafe_allow_html=True,
)


st.subheader("1. Filtro por etiqueta")

if get_mock_mode():
    st.error("❌​ El modo simulación no soporta filtrado por etiquetas.")
elif is_filter_active() and not get_mock_mode():
    tag = get_tag_filter()
    st.success(
        f"🏷️ Se aplicará el filtro **{tag['key']}** = `{tag['value']}` "
        f"en los servicios que lo soporten.",
    )
else:
    st.info(
        "No hay filtro activo. El informe incluirá todos los recursos de la cuenta. "
        "Puede activar un filtro desde el panel lateral antes de generar.",
        icon="ℹ️",
    )

st.divider()
st.subheader("2. Secciones a incluir")
st.caption("Desmarque las secciones que no quiera incluir en el informe.")

# Checkboxes por sección agrupados en dos columnas
section_keys = list(SECTIONS.keys())
selected = {}

col1, col2 = st.columns(2)

for i, key in enumerate(section_keys):
    col = col1 if i % 2 == 0 else col2
    with col:
        selected[key] = st.checkbox(
            SECTIONS[key]["label"],
            value=True,
            key=f"sec_{key}",
        )

st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)

st.markdown("**Opcional avanzado**")
is_mock_mode = get_mock_mode()
include_charts = st.toggle(
    "📊 Incluir gráficas de métricas en el informe",
    value=not is_mock_mode,
    disabled=is_mock_mode,
    help="Incrusta los gráficos de CPU y memoria como imágenes en el Markdown. "
         "Desactívelo para un informe más ligero o compatible con GitHub.",
)

if is_mock_mode:
    st.info(
        "En modo simulación, las gráficas se desactivan para evitar informes demasiado pesados "
        "que pueden bloquear la vista previa.",
        icon="ℹ️",
    )

selected_sections = [k for k, v in selected.items() if v]

st.divider()
st.subheader("3. Generar informe")

n_selected = len(selected_sections)
st.caption(f"{n_selected} de {len(SECTIONS)} secciones seleccionadas.")

if n_selected == 0:
    st.warning("Seleccione al menos una sección para generar el informe.")
    st.stop()

if st.button("⚙️ Generar informe", type="primary", width='stretch'):
    with st.spinner("Recopilando datos de todos los servicios seleccionados..."):
        effective_include_charts = include_charts and (not is_mock_mode)
        report_md = build_report(selected_sections, include_charts=effective_include_charts)

    st.success("✅ Informe generado correctamente.")

    # Nombre de archivo con timestamp para evitar sobreescrituras, y opcionalmente con el tag aplicado
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    tag = get_tag_filter()
    tag_suffix = f"_{tag['value']}" if tag else ""
    filename = f"informe_aws{tag_suffix}_{now_str}.md"

    st.download_button(
        label="⬇️ Descargar informe Markdown",
        data=report_md,
        file_name=filename,
        mime="text/markdown",
        width='stretch',
    )

    # Vista previa colapsable
    with st.expander("👁️ Vista previa del informe", expanded=False):
        if len(report_md) > 500_000:
            st.warning(
                "La vista previa se omitió porque el informe es demasiado grande. "
                "Descárguelo para revisarlo completo.",
                icon="⚠️",
            )
        else:
            st.markdown(report_md)
