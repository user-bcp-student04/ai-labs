# api/app/schemas.py
"""Modelos Pydantic de salida. No exponen estructuras internas."""
from typing import Literal

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
