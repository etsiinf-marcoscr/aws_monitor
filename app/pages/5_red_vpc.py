import streamlit as st

from aws.vpc import (
    get_vpcs_dataframe,
    get_subnets_dataframe,
    get_route_tables_dataframe,
    get_routes_by_table_dataframe,
    get_security_groups_dataframe,
    get_internet_gateways_dataframe,
    get_nat_gateways_dataframe,
    get_load_balancers_dataframe,
)
from utils.tag_filter import get_tag_filter

st.set_page_config(page_title="VPC", layout="wide")

st.title("Virtual Private Cloud (VPC)")

vpcs = get_vpcs_dataframe()

st.subheader("VPCs encontradas")

st.dataframe(
    vpcs,
    width="stretch",
    hide_index=True,
    column_config={
        "Nombres de host DNS": st.column_config.CheckboxColumn("Nombres de host DNS"),
        "Resolución de DNS":   st.column_config.CheckboxColumn("Resolución de DNS"),
    },
)

if vpcs.empty:
    tag_filter = get_tag_filter()
    if tag_filter:
        all_vpcs = get_vpcs_dataframe(apply_tag_filter=False)
        if all_vpcs.empty:
            st.info("No se encontraron VPCs para monitorizar.")
        else:
            st.info(
                f"No se encontraron VPCs con la etiqueta "
                f"**{tag_filter['key']}** = `{tag_filter['value']}`."
            )
    else:
        st.info("No se encontraron VPCs para monitorizar.")

else:

    selected_vpc = st.selectbox(
        "Selecciona una VPC",
        vpcs["VPC ID"]
    )

    st.subheader("Información VPC")

    st.dataframe(
        vpcs[vpcs["VPC ID"] == selected_vpc],
        width="stretch"
    )

    subnets = get_subnets_dataframe(selected_vpc)
    routes = get_route_tables_dataframe(selected_vpc)
    sgs = get_security_groups_dataframe(selected_vpc)
    igw = get_internet_gateways_dataframe(selected_vpc)
    nat = get_nat_gateways_dataframe(selected_vpc)
    lbs = get_load_balancers_dataframe(selected_vpc)
    alb_count = len(lbs[lbs["Tipo"] == "application"]) if not lbs.empty and "Tipo" in lbs.columns else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Subredes", len(subnets))
    col2.metric("Tablas de Ruta", len(routes))
    col3.metric("Grupos de Seguridad", len(sgs))
    col4.metric("Gateways", len(igw) + len(nat))
    col5.metric("Balanceadores de Carga", len(lbs))

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Subredes",
        "Tablas de Ruta",
        "Grupos de Seguridad",
        "Pasarelas a Internet (IGW)",
        "Pasarelas NAT (NATGW)",
        "Balanceadores de Carga",
    ])

    with tab1:
        st.dataframe(subnets, width="stretch")

    with tab2:
        st.dataframe(routes, width="stretch", hide_index=True)

        if not routes.empty:
            st.markdown("#### Rutas de la tabla seleccionada")
            selected_rtb = st.selectbox(
                "Selecciona una tabla de ruta",
                routes["Route Table ID"],
                key="selectbox_rtb",
            )
            route_details = get_routes_by_table_dataframe(selected_rtb)

            if route_details.empty:
                st.info("No se encontraron rutas para esta tabla.")
            else:
                col_in, col_out = st.columns(2)

                with col_in:
                    st.markdown("**Rutas de entrada**")
                    df_in = route_details[route_details["Dirección"] == "Entrada"]
                    if df_in.empty:
                        st.caption("Sin rutas de entrada.")
                    else:
                        st.dataframe(df_in.drop(columns="Dirección"), hide_index=True)

                with col_out:
                    st.markdown("**Rutas de salida**")
                    df_out = route_details[route_details["Dirección"] == "Salida"]
                    if df_out.empty:
                        st.caption("Sin rutas de salida.")
                    else:
                        st.dataframe(df_out.drop(columns="Dirección"), hide_index=True)

    with tab3:
        st.dataframe(sgs, width="stretch")

    with tab4:
        st.dataframe(igw, width="stretch")

    with tab5:
        st.dataframe(nat, width="stretch")

    with tab6:
        if lbs.empty:
            st.info("No se encontraron load balancers en esta VPC.")
        else:
            st.dataframe(lbs, width="stretch")
