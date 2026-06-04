import streamlit as st

from aws.s3 import (
    get_buckets_dataframe,
    get_objects_dataframe,
    get_bucket_size_metrics,
    get_request_metrics,
)
from utils.tag_filter import get_tag_filter

st.set_page_config(
    page_title="S3",
    layout="wide",
)

st.title("Simple Storage Service (S3)")


st.header("Buckets")

buckets_df = get_buckets_dataframe()

if buckets_df.empty:
    tag_filter = get_tag_filter()
    if tag_filter:
        all_buckets_df = get_buckets_dataframe(apply_tag_filter=False)
        if all_buckets_df.empty:
            st.info("No se encontraron buckets S3 para monitorizar.")
        else:
            st.info(
                f"No se encontraron buckets S3 con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
    else:
        st.info("No se encontraron buckets S3 para monitorizar.")
    st.stop()

st.dataframe(buckets_df)

selected_bucket = st.selectbox(
    "Seleccionar bucket",
    buckets_df["Bucket"],
)


st.header("Objetos")

# Navegación por prefijo (carpetas virtuales)
prefix = st.text_input("Prefijo / carpeta (dejar vacío para la raíz)", value="")

objects_df = get_objects_dataframe(selected_bucket, prefix)

if objects_df.empty:
    st.info("El bucket está vacío o no hay objetos bajo este prefijo.")
else:
    st.dataframe(objects_df)


st.header("Tamaño del bucket (últimos 14 días)")

size_df = get_bucket_size_metrics(selected_bucket)

if not size_df.empty:
    st.line_chart(size_df.set_index("instante")["tamaño_gb"], y_label="GB")
else:
    st.info("No hay datos de tamaño disponibles (la métrica se publica una vez al día).")

st.header("Número de objetos (últimas 24 h)")

objects_metric_df = get_request_metrics(selected_bucket)

if not objects_metric_df.empty:
    st.line_chart(objects_metric_df.set_index("instante")["objetos"])
else:
    st.info("No hay datos de número de objetos disponibles.")
