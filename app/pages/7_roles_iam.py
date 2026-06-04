import streamlit as st

from aws.iam import (
    get_account_summary,
    get_users_dataframe,
    get_roles_dataframe,
    get_policies_dataframe,
)
from utils.tag_filter import is_filter_active
from config import get_mock_mode

st.set_page_config(
    page_title="IAM",
    layout="wide"
)

if is_filter_active() and not get_mock_mode():
    st.warning(
        "El filtro por etiqueta no aplica en IAM. "
        "Es un servicio global de cuenta independiente de los stacks desplegados.",
        icon="⚠️",
    )

st.title("Identity and Access Management (IAM)")

summary = get_account_summary()

if summary:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Usuarios", summary["Usuarios"])
    col2.metric("Roles", summary["Roles"])
    col3.metric("Políticas", summary["Políticas"])
    col4.metric("Usuarios con MFA", summary["Usuarios con MFA"])
    col5.metric("MFA root", summary["MFA root habilitado"])

tab1, tab2, tab3 = st.tabs(["Usuarios", "Roles", "Políticas"])

with tab1:
    st.subheader("Usuarios IAM")
    users = get_users_dataframe()
    if users.empty:
        st.info("No se encontraron usuarios.")
    else:
        st.dataframe(users, width="stretch")

with tab2:
    st.subheader("Roles IAM")
    roles = get_roles_dataframe()
    if roles.empty:
        st.info("No se encontraron roles.")
    else:
        st.dataframe(roles, width="stretch")

with tab3:
    st.subheader("Políticas IAM")
    policies = get_policies_dataframe()
    if policies.empty:
        st.info("No se encontraron políticas.")
    else:
        st.dataframe(policies, width="stretch")