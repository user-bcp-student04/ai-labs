# api/app/services.py
"""Lógica de negocio. Aquí solo existe el estado del servicio."""
from app import config
from app.schemas import HealthResponse


def get_health() -> HealthResponse:
    return HealthResponse(status="ok", service=config.SERVICE_NAME)
