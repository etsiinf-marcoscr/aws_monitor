import streamlit as st
from aws.sns import (
    get_topics_dataframe,
    get_subscriptions_dataframe,
    get_publish_metrics
)
from utils.tag_filter import get_tag_filter

st.set_page_config(
    page_title="SNS",
    layout="wide"
)

st.title("Simple Notification Service (SNS)")

topics_df = get_topics_dataframe()

if topics_df.empty:
    tag_filter = get_tag_filter()
    if tag_filter:
        all_topics_df = get_topics_dataframe(apply_tag_filter=False)
        if all_topics_df.empty:
            st.info("No se encontraron Temas SNS para monitorizar.")
        else:
            st.info(
                f"No se encontraron Temas SNS con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
    else:
        st.info("No se encontraron Temas SNS para monitorizar.")
    st.stop()

st.header("Temas")
st.dataframe(topics_df, width="stretch")

selected_topic = st.selectbox(
    "Seleccionar Tema",
    topics_df["Nombre"]
)

topic_arn = topics_df.loc[topics_df["Nombre"] == selected_topic, "ARN del Tema"].iloc[0]

try:
    tab_subs, tab_metrics = st.tabs(["Suscripciones", "Métricas"])
    with tab_subs:
        st.subheader("Suscripciones del Tema")

        subs_df = get_subscriptions_dataframe(topic_arn)

        if subs_df.empty:
            st.info("No se encontraron suscripciones para este Tema.")
        else:
            st.dataframe(subs_df, width="stretch")

    with tab_metrics:
        st.subheader("Publicaciones (última hora)")
        published_df = get_publish_metrics(topic_arn)

        if not published_df.empty:
            st.line_chart(published_df.set_index("instante")["Publicaciones"])
except Exception:
    st.subheader("Suscripciones del Tema")
    subs_df = get_subscriptions_dataframe(topic_arn)

    if subs_df.empty:
        st.info("No se encontraron suscripciones para este Tema.")
    else:
        st.dataframe(subs_df, width="stretch")

    st.subheader("Publicaciones (última hora)")
    published_df = get_publish_metrics(topic_arn)

    if not published_df.empty:
        st.line_chart(published_df.set_index("instante")["Publicaciones"]) 
