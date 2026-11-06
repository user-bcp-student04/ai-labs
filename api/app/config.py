# api/app/config.py
"""Configuración leída de variables de entorno, con valores por defecto."""
import os

SERVICE_NAME: str = os.getenv("SERVICE_NAME", "merchant-qr-api")
API_VERSION: str = os.getenv("API_VERSION", "0.1.0")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
