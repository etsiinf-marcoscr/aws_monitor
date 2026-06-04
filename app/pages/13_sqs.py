import streamlit as st
from aws.sqs import (
    get_queues_dataframe,
    get_queue_attributes_dataframe,
    get_messages_sent_metrics,
    get_messages_received_metrics,
    get_messages_deleted_metrics
)
from utils.tag_filter import get_tag_filter

st.set_page_config(
    page_title="SQS",
    layout="wide"
)

st.title("Simple Queue Service (SQS)")

queues_df = get_queues_dataframe()

if queues_df.empty:
    tag_filter = get_tag_filter()
    if tag_filter:
        all_queues_df = get_queues_dataframe(apply_tag_filter=False)
        if all_queues_df.empty:
            st.info("No se encontraron Colas SQS para monitorizar.")
        else:
            st.info(
                f"No se encontraron Colas SQS con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
    else:
        st.info("No se encontraron Colas SQS para monitorizar.")
    st.stop()

st.header("Colas")
st.dataframe(queues_df, width="stretch")

selected_queue = st.selectbox(
    "Seleccionar Cola",
    queues_df["Nombre"]
)

queue_url = queues_df.loc[queues_df["Nombre"] == selected_queue, "URL de Cola"].iloc[0]
queue_name = selected_queue

try:
    tab_attrs, tab_metrics = st.tabs(["Atributos", "Métricas"])

    with tab_attrs:
        st.subheader("Atributos de la Cola")
        attrs_df = get_queue_attributes_dataframe(queue_url)

        if attrs_df.empty:
            st.info("No se encontraron atributos para esta Cola.")
        else:
            st.dataframe(attrs_df, width="stretch")

    with tab_metrics:
        st.subheader("Mensajes enviados (última hora)")
        sent_df = get_messages_sent_metrics(queue_name)
        if not sent_df.empty:
            st.line_chart(sent_df.set_index("instante")["Mensajes Enviados"]) 

        st.subheader("Mensajes recibidos (última hora)")
        recv_df = get_messages_received_metrics(queue_name)
        if not recv_df.empty:
            st.line_chart(recv_df.set_index("instante")["Mensajes Recibidos"]) 

        st.subheader("Mensajes eliminados (última hora)")
        del_df = get_messages_deleted_metrics(queue_name)
        if not del_df.empty:
            st.line_chart(del_df.set_index("instante")["Mensajes Eliminados"]) 

except Exception:
    st.subheader("Atributos de la Cola")
    attrs_df = get_queue_attributes_dataframe(queue_url)

    if attrs_df.empty:
        st.info("No se encontraron atributos para esta Cola.")
    else:
        st.dataframe(attrs_df, width="stretch")

    st.subheader("Mensajes enviados (última hora)")
    sent_df = get_messages_sent_metrics(queue_name)
    if not sent_df.empty:
        st.line_chart(sent_df.set_index("instante")["Mensajes Enviados"]) 

    st.subheader("Mensajes recibidos (última hora)")
    recv_df = get_messages_received_metrics(queue_name)
    if not recv_df.empty:
        st.line_chart(recv_df.set_index("instante")["Mensajes Recibidos"]) 

    st.subheader("Mensajes eliminados (última hora)")
    del_df = get_messages_deleted_metrics(queue_name)
    if not del_df.empty:
        st.line_chart(del_df.set_index("instante")["Mensajes Eliminados"]) 
