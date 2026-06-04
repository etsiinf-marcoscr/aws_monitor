import streamlit as st
from pathlib import Path
from components.filter_slot import render_tag_filter_panel
from components.credentials_slot import render_aws_credentials_panel
from components.refresh_button import render_refresh_button

st.set_page_config(
    page_title="AWS Monitor",
    page_icon="☁️",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Ajusta tamaño del logo nativo de Streamlit en sidebar. */
    section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] img,
    section[data-testid="stSidebar"] [data-testid="stLogo"] img {
        height: 2.4rem !important;
        width: auto !important;
        max-height: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def render_sidebar_logo() -> None:
    """Pinta el logo en la cabecera nativa del sidebar."""
    logo_path = Path(__file__).resolve().parent / "assets" / "logo_aws_monitor_wordmark.svg"
    if not logo_path.exists():
        return

    try:
        st.logo(str(logo_path))
    except Exception:
        st.sidebar.image(str(logo_path), width='stretch')


render_sidebar_logo()
render_refresh_button()
render_tag_filter_panel()
render_aws_credentials_panel()

selected_vpc = st.query_params.get("selected_vpc")
if isinstance(selected_vpc, list):
    selected_vpc = selected_vpc[0]

if selected_vpc:
    st.session_state["selected_vpc_transfer"] = selected_vpc
    vpc_page = st.Page("pages/5_red_vpc.py", title="VPC", icon=":material/hub:")
    st.switch_page(vpc_page)


def render_home_page():
    """Renderiza la portada principal de la aplicacion."""
    st.title("AWS Monitor - Página Principal")

    st.markdown("""
    Bienvenido al panel de monitorización de servicios AWS.

    Navega por las secciones del menú lateral.
    """)


if hasattr(st, "navigation"):
    pages = [
        st.Page(render_home_page, title="Inicio", icon=":material/home:", visibility="hidden"), # pruebas de página de inicio personalizada
        st.Page("pages/1_dashboard.py", title="Panel de control", icon=":material/monitoring:", default=True),
        st.Page("pages/2_contenedores_ecs.py", title="ECS", icon=":material/widgets:"),
        st.Page("pages/3_contenedores_ecr.py", title="ECR", icon=":material/inventory_2:"),
        st.Page("pages/17_s3.py", title="S3", icon=":material/cleaning_bucket:"),
        st.Page("pages/4_bases_datos_rds.py", title="RDS", icon=":material/storage:"),
        st.Page("pages/14_dynamodb.py", title="DynamoDB", icon=":material/database:"),
        st.Page("pages/5_red_vpc.py", title="VPC", icon=":material/hub:"),
        st.Page("pages/6_grupos_seguridad.py", title="Grupos de Seguridad", icon=":material/security:"),
        st.Page("pages/7_roles_iam.py", title="Permisos IAM", icon=":material/admin_panel_settings:"),
        st.Page("pages/11_cognito.py", title="Cognito", icon=":material/lock:"),
        st.Page("pages/12_sns.py", title="SNS", icon=":material/notifications:"),
        st.Page("pages/13_sqs.py", title="SQS", icon=":material/inbox:"),
        st.Page("pages/18_elasticache.py", title="ElastiCache", icon=":material/memory:"),
        st.Page("pages/8_costes.py", title="Costes", icon=":material/payments:"),
        st.Page("pages/9_despliegues_cloudformation.py", title="CloudFormation", icon=":material/deployed_code:"),
        st.Page("pages/10_arquitectura_conexiones.py", title="Arquitectura y Conexiones", icon=":material/schema:"),
        st.Page("pages/15_mapa.py", title="Mapa de Servicios", icon=":material/map:"),
        st.Page("pages/16_informe_aws.py", title="Informe AWS", icon=":material/description:"),
        st.Page("pages/19_cloudwatch.py", title="Registros CloudWatch", icon=":material/article:"),
    ]
    st.navigation(pages, position="sidebar").run()
else:
    render_home_page()
