import streamlit as st
from aws.cognito import (
    get_user_pools_dataframe,
    get_user_pool_clients_dataframe,
    get_users_dataframe,
    get_user_counts,
    get_sign_in_metrics,
    get_sign_up_metrics
)
from utils.tag_filter import get_tag_filter

st.set_page_config(
    page_title="Cognito",
    layout="wide"
)

st.title("Cognito - Grupos de Usuarios (User Pools)")

pools_df = get_user_pools_dataframe()

if pools_df.empty:
    tag_filter = get_tag_filter()
    if tag_filter:
        all_pools_df = get_user_pools_dataframe(apply_tag_filter=False)
        if all_pools_df.empty:
            st.info("No se encontraron Grupos de Usuarios de Cognito para monitorizar.")
        else:
            st.info(
                f"No se encontraron Grupos de Usuarios de Cognito con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
    else:
        st.info("No se encontraron Grupos de Usuarios de Cognito para monitorizar.")
    st.stop()

st.header("Grupos de Usuarios")
st.dataframe(pools_df, width="stretch")

selected_pool = st.selectbox(
    "Seleccionar Grupo de Usuarios",
    pools_df["Grupo de Usuarios"]
)

pool_id = pools_df.loc[pools_df["Grupo de Usuarios"] == selected_pool, "ID"].iloc[0]


try:
    tab_clients, tab_users, tab_metrics = st.tabs(["Clientes de Aplicación", "Usuarios", "Métricas"])

    with tab_clients:
        st.subheader("Clientes de Aplicación del Grupo")

        clients_df = get_user_pool_clients_dataframe(pool_id)

        if clients_df.empty:
            st.info("No se encontraron clientes de aplicación para este Grupo.")
        else:
            st.dataframe(clients_df, width="stretch")

    with tab_users:
        st.subheader("Usuarios del Grupo")

        users_df = get_users_dataframe(pool_id)

        if users_df.empty:
            st.info("No se encontraron usuarios para este Grupo.")
        else:
            st.dataframe(users_df, width="stretch")

    with tab_metrics:
        st.subheader("Estadísticas del Grupo")

        stats = get_user_counts(pool_id)

        if stats:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Usuarios totales", stats.get("total", 0))
            c2.metric("Confirmados", stats.get("confirmed", 0))
            c3.metric("Habilitados", stats.get("enabled", 0))
            c4.metric("Deshabilitados", stats.get("disabled", 0))

        st.markdown("---")

        st.subheader("Inicios de sesión (última hora)")
        signins_df = get_sign_in_metrics(pool_id)

        if not signins_df.empty:
            st.line_chart(signins_df.set_index("instante")["Inicios de Sesión"]) 

        st.subheader("Registros (última hora)")
        signups_df = get_sign_up_metrics(pool_id)

        if not signups_df.empty:
            st.line_chart(signups_df.set_index("instante")["Registros"]) 
except Exception:
    tab_clients, tab_users = st.tabs(["Clientes de Aplicación", "Usuarios"])

    with tab_clients:
        st.subheader("Clientes de Aplicación del Grupo")

        clients_df = get_user_pool_clients_dataframe(pool_id)

        if clients_df.empty:
            st.info("No se encontraron clientes de aplicación para este Grupo.")
        else:
            st.dataframe(clients_df, width="stretch")

    with tab_users:
        st.subheader("Usuarios del Grupo")

        users_df = get_users_dataframe(pool_id)

        if users_df.empty:
            st.info("No se encontraron usuarios para este Grupo.")
        else:
            st.dataframe(users_df, width="stretch")

    with st.expander("Métricas"):
        st.subheader("Estadísticas del Grupo")

        stats = get_user_counts(pool_id)

        if stats:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Usuarios totales", stats.get("total", 0))
            c2.metric("Confirmados", stats.get("confirmed", 0))
            c3.metric("Habilitados", stats.get("enabled", 0))
            c4.metric("Deshabilitados", stats.get("disabled", 0))

        st.markdown("---")

        st.subheader("Inicios de sesión (última hora)")
        signins_df = get_sign_in_metrics(pool_id)

        if not signins_df.empty:
            st.line_chart(signins_df.set_index("instante")["Inicios de Sesión"]) 

        st.subheader("Registros (última hora)")
        signups_df = get_sign_up_metrics(pool_id)

        if not signups_df.empty:
            st.line_chart(signups_df.set_index("instante")["Registros"]) 
