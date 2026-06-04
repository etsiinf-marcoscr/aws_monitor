import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")


def _env_bool(name, default=False):
	"""Lee una variable de entorno booleana con fallback a valor por defecto."""
	return os.getenv(name, str(default)).lower() == "true"


def get_mock_mode():
	"""Obtiene el estado de MOCK_MODE priorizando session_state sobre .env."""
	try:
		session_value = st.session_state.get("mock_mode")
	except Exception:
		session_value = None

	if session_value is not None:
		return bool(session_value)

	return _env_bool("MOCK_MODE", False)