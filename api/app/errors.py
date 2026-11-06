# api/app/errors.py
"""Handlers de error con un único formato JSON: {"code", "message"}."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")

_CODES: dict[int, str] = {
    400: "INVALID_INPUT",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
}

_MESSAGES: dict[int, str] = {
    400: "Entrada inválida.",
    401: "Autenticación requerida.",
    403: "No tienes permisos para esta operación.",
    404: "Recurso no encontrado.",
    405: "Método no permitido.",
    409: "Conflicto con el estado actual del recurso.",
    413: "El contenido enviado supera el tamaño permitido.",
    422: "Entrada inválida.",
}


def _error(status: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"code": code, "message": message},
        headers=headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    status = exc.status_code
    code = _CODES.get(status, "INTERNAL_ERROR" if status >= 500 else "HTTP_ERROR")
    # Se usa el detalle solo si es texto y no es un error de servidor.
    if isinstance(exc.detail, str) and exc.detail and status < 500 and status not in _MESSAGES:
        message = exc.detail
    else:
        message = _MESSAGES.get(status, "Error en la solicitud." if status < 500 else "Error interno del servidor.")
    return _error(status, code, message, dict(exc.headers) if exc.headers else None)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Solo nombres de campo; nunca los valores enviados por el cliente.
    fields = sorted({".".join(str(part) for part in err.get("loc", ())) for err in exc.errors()})
    detail = ", ".join(f for f in fields if f) or "solicitud"
    return _error(422, "VALIDATION_ERROR", f"Entrada inválida en: {detail}.")


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # La traza queda solo en el log del servidor; la respuesta es genérica.
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return _error(500, "INTERNAL_ERROR", "Error interno del servidor.")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
