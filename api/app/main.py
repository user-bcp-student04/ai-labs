# api/app/main.py
"""Crea la app FastAPI, registra routers y handlers de error."""
import logging

from fastapi import FastAPI

from app import config
from app.errors import register_error_handlers
from app.routers import health

logging.basicConfig(level=config.LOG_LEVEL)

app = FastAPI(title=config.SERVICE_NAME, version=config.API_VERSION)
register_error_handlers(app)
app.include_router(health.router)
