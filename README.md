# TFG - AWS Monitor
### Autor: Marcos Casado Ruiz
Aplicación web de monitorización de infraestructuras AWS desarrollada en Python utilizando **Streamlit** y **boto3**.

El objetivo del proyecto es visualizar el estado y métricas de arquitecturas basadas en **contenedores en AWS**.

La aplicación permite inspeccionar recursos desplegados, ver métricas de rendimiento, explorar la red (VPC, Security Groups) y estimar costes de infraestructura.

## Requisitos

- Python 3.11+
- Credenciales AWS con permisos de lectura para los servicios utilizados (ECS, ECR, RDS, CloudWatch, etc.)

## Instalación

```bash
python -m venv venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env
# Edita .env con tus credenciales AWS
```

## Arranque

```bash
streamlit run app/
python -m streamlit run app/ (en caso de problemas con el PATH)
```

## Modo simulación (sin crédito AWS)

En el archivo `.env`, cambia:

```
MOCK_MODE=true
```

La aplicación arrancará con datos ficticios sin hacer ninguna llamada a AWS.

## Credenciales AWS desde la interfaz

En la barra lateral encontrarás un bloque de perfil AWS donde puedes introducir `Access key ID`, `Secret access key`, `Session token (opcional)` y `Region`.

Los valores guardados ahí sobrescriben los del `.env` mientras dure la sesión de Streamlit. Si prefieres volver a los valores del fichero de entorno, puedes usar el botón de restablecer dentro del mismo panel.

## Arquitectura del proyecto

El proyecto sigue una estructura modular para separar:

- interfaz (Streamlit)
- acceso a AWS
- utilidades
- componentes visuales
- datos simulados (mock)
