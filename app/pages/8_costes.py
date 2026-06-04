import streamlit as st
import pandas as pd

from aws.costs import estimate_costs, estimate_costs_by_day
from config import get_mock_mode
from utils.tag_filter import get_tag_filter, is_filter_active

st.set_page_config(page_title="Costes", layout="wide")

st.title("Coste aproximado de los recursos AWS")

# Aviso de filtro activo por tag
if is_filter_active() and not get_mock_mode():
    tag = get_tag_filter()
    st.info(
        f"Mostrando costes filtrados por etiqueta **{tag['key']}** = `{tag['value']}`.",
        icon="🏷️",
    )

st.caption(f"Periodo: mes en curso")

@st.cache_data(ttl=300)  # Cost Explorer tiene latencia y coste por llamada
def load_costs():
    return estimate_costs(), estimate_costs_by_day()

with st.spinner("Consultando Cost Explorer..."):
    costs_df, daily_df = load_costs()

# Asegura que el dataframe está ordenado por coste descendente
costs_df = costs_df.sort_values("Coste mensual ($)", ascending=False)

if costs_df.empty:
    st.info("No hay datos de costes disponibles para el periodo actual.")
    st.stop()

total = costs_df["Coste mensual ($)"].sum()
servicio_top = costs_df.iloc[0]["Servicio"] if not costs_df.empty else "-"
coste_top = costs_df.iloc[0]["Coste mensual ($)"] if not costs_df.empty else 0

col1, col2, col3 = st.columns([1, 2, 1])
col1.metric("Coste total del mes", f"${round(total, 2)}")
col2.metric("Servicio más costoso", servicio_top)
col3.metric("Coste del servicio más costoso", f"${coste_top}")

st.divider()


tab1, tab2 = st.tabs(["Por servicio", "Evolución diaria"])

with tab1:
    col_chart, col_table = st.columns([1, 1])

    with col_chart:
        st.subheader("Distribución por servicio")
        # Nombres cortos para el gráfico
        chart_df = costs_df.copy()
        chart_df["Servicio"] = chart_df["Servicio"].str.replace("Amazon ", "").str.replace("AWS ", "")
        st.bar_chart(
            chart_df.set_index("Servicio")["Coste mensual ($)"],
            width='stretch',
        )

    with col_table:
        st.subheader("Tabla de costes")
        st.dataframe(
            costs_df.reset_index(drop=True),
            width='stretch',
            hide_index=True,
        )

with tab2:
    st.subheader("Evolución del gasto diario")

    if daily_df.empty:
        st.info("No hay datos de evolución diaria disponibles.")
    else:
        col_daily, col_accum = st.columns(2)

        with col_daily:
            st.caption("Coste diario ($)")
            st.bar_chart(
                daily_df.set_index("Fecha")["Coste diario ($)"],
                width='stretch',
            )

        with col_accum:
            st.caption("Coste acumulado ($)")
            st.line_chart(
                daily_df.set_index("Fecha")["Coste acumulado ($)"],
                width='stretch',
            )

