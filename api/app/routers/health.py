# api/app/routers/health.py
"""Router delgado: sin lógica de negocio."""
from fastapi import APIRouter

from app import services
from app.schemas import ErrorResponse, HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={500: {"model": ErrorResponse}},
)
def health() -> HealthResponse:
    return services.get_health()
