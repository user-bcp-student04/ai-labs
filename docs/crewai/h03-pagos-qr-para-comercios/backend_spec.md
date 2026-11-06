# backend_spec.md

## 1. Resumen de la solución

**H03 no requiere endpoints ni persistencia en el servidor FastAPI.** El plan aprobado de Arquitectura (S-1, C8) fija que:

- El navegador decodifica el QR y llama directamente a W3 `POST /qrs/resolve` y a W2 `POST /payments`, además de las consultas de estado y recibo.
- El historial es local, en el navegador.
- La capa `api/app/` no cambia y no se añaden `routers/`, `services.py`, `schemas.py` ni `config.py` nuevos para H03.

Por lo tanto **no implemento ningún endpoint de negocio**. Hacerlo (por ejemplo, un proxy hacia W2/W3) cambiaría la arquitectura aprobada y el Issue no lo pide.

Para cumplir el entregable (código extraíble, configuración, dependencias y casos verificables) incluyo una **base mínima** con lo que el backend debe garantizar en cualquier caso:

- un formato de error único `{"code","message"}`;
- configuración por variables de entorno;
- un único endpoint técnico `GET /health`, que **no forma parte del contrato de H03** y existe solo para tener un caso válido comprobable.

> **Si `api/app/` ya existe en el repositorio, no sobrescribas sus archivos.** Integra solo lo que falte y elimina `/health` si no lo quieres. No conozco el estado actual del repositorio (ver P-2 del Arquitecto).

Nada de lo siguiente se ha ejecutado. Todo resultado de la sección 8 está marcado **NO EJECUTADO**.

## 2. Stack y estructura de archivos

- Python con FastAPI (Starlette) y Pydantic v2, servido con uvicorn. **No se usa Java, Quarkus ni Maven.** Ningún documento previo contradice el stack del Issue.

```text
api/
├── requirements.txt
└── app/
    ├── __init__.py
    ├── main.py          # crea la app, registra routers y handlers
    ├── config.py        # configuración por variables de entorno
    ├── errors.py        # handlers de error con formato único
    ├── schemas.py       # modelos Pydantic de salida
    ├── services.py      # lógica (estado del servicio)
    └── routers/
        ├── __init__.py
        └── health.py    # router delgado
```

## 3. Tabla de endpoints

| Método | Ruta | Entrada | Respuesta | Errores |
|---|---|---|---|---|
| GET | `/health` (técnico, fuera del contrato H03) | ninguna | 200 `{"status":"ok","service":"<SERVICE_NAME>"}` | 404 `NOT_FOUND` en rutas inexistentes; 405 `METHOD_NOT_ALLOWED` con otro método; 500 `INTERNAL_ERROR` en fallos inesperados |

**Endpoints de H03 (W3 `POST /qrs/resolve`, W2 `POST /payments`, estado, recibo):** son servicios externos (mock de solo lectura) consumidos por el frontend. **No se implementan aquí** y su contrato sigue pendiente de P-1.

## 4. Reglas de validación

- `/health` no recibe entrada. FastAPI rechaza con 422 `VALIDATION_ERROR` cualquier parámetro mal tipado que se declare en el futuro.
- Reglas que **sí aplicarían** si una historia futura moviera lógica al backend (hoy no hay código para ellas):
  - Importe positivo para QR de monto abierto, con `Field(gt=0)`.
  - Payload textual con `max_length` (límite pendiente en P-6).
  - Sin datos binarios de imagen.
- La validación del cliente (botón deshabilitado, etc.) **no sustituye** a la del servidor que sí valida (el mock W2/W3).

## 5. Manejo de errores

Un único formato JSON, `{"code": "...", "message": "..."}`, con `exception_handler` registrados para:

- `HTTPException` (la de Starlette, para capturar también los 404/405 del enrutador);
- `RequestValidationError`;
- `Exception`.

| HTTP | `code` |
|---|---|
| 400 | `INVALID_INPUT` |
| 401 | `UNAUTHORIZED` |
| 403 | `FORBIDDEN` |
| 404 | `NOT_FOUND` |
| 405 | `METHOD_NOT_ALLOWED` |
| 409 | `CONFLICT` |
| 413 | `PAYLOAD_TOO_LARGE` |
| 422 | `VALIDATION_ERROR` |
| 500 | `INTERNAL_ERROR` |

- El mensaje de 422 lista solo los nombres de los campos inválidos, nunca los valores enviados.
- El 500 devuelve un mensaje genérico. La traza se registra solo en el log del servidor, sin rutas, SQL ni secretos en la respuesta.
- Los códigos de negocio de H03 (`QR_INVALID`, `QR_EXPIRED`, `QR_CONFLICT`, etc.) pertenecen al contrato supuesto de W2/W3 y los traduce el frontend (S-4). No se generan aquí.

## 6. Límites, archivos, identidad y concurrencia

- **Subidas y límite de tamaño: no aplica.** La imagen QR se decodifica en el navegador y solo viaja el payload textual a W3. No hay `multipart` ni middleware de conteo de bytes. Si P-6 fija un límite de payload y algo pasa por este backend, habrá que añadir un límite en `config.py` y un middleware ASGI.
- **Identidad y aislamiento por propietario: no aplica.** No hay usuarios ni archivos por propietario en esta historia (S-6). No se usa hash SHA-256 ni directorios por propietario, y no se expone ningún valor derivado.
- **Concurrencia en servidor: no aplica.** `/health` no tiene estado. La concurrencia entre pestañas del historial local es responsabilidad del frontend (sección 2.1 del Arquitecto).
- **Archivos preexistentes: no aplica**, porque este backend no escribe en disco.

## 7. Origen de la persistencia

- **No hay base de datos en este Issue.** No hay contrato de Datos aprobado en el contexto y el Issue no usa persistencia en servidor, por lo que **no emito SQL ni migraciones**.
- El historial vive en el almacenamiento del navegador con `schemaVersion: 1` (S-7). Lo implementa el frontend.
- No hay transacciones de servidor.

## 8. Recorrido de un caso válido y de un caso de error

**Caso válido (`GET /health`)**
1. uvicorn recibe la petición.
2. FastAPI la enruta a `routers/health.py`.
3. El router llama a `services.get_health()`.
4. El servicio devuelve el estado con el nombre del servicio leído de `config.py`.
5. FastAPI serializa con `HealthResponse` y responde 200.
6. No hay lectura ni escritura de almacenamiento.

**Caso de error (`GET /no-existe`)**
1. El enrutador no encuentra la ruta y lanza `HTTPException(404)`.
2. El handler de `errors.py` lo convierte a `{"code":"NOT_FOUND","message":"Recurso no encontrado."}` con HTTP 404.
3. No se toca almacenamiento.

## 9. Supuestos y pendientes

- **Stack:** el Issue manda: Python/FastAPI. Ningún documento previo indica Java ni Quarkus.
- **S-1 (Arquitecto):** `api/app/` no cambia por H03. Este entregable es solo una base mínima. **Pendiente de confirmar:** si el repositorio ya la tiene, descartar estos archivos.
- **`/health`:** es un endpoint técnico añadido por mí solo para poder verificar un caso válido. No es contrato de H03; elimínalo si no se acepta.
- **Dependencias:** el Issue no es una actualización de dependencias. Los pines de `api/requirements.txt` son **mi propuesta y NO están verificados** contra PyPI/OSV a fecha 2026-11-06. Si el repositorio ya tiene `requirements.txt`, conserva el existente. Pendiente: que Arquitectura o Seguridad confirmen versiones. Hice los pines coherentes entre sí (`fastapi 0.115.6` admite `starlette >=0.40,<0.42`), pero **no ejecuté `pip install` ni `pip check`**.
- **Contrato W2/W3 (P-1), P-2, P-3, P-4, P-5, P-6, P-7, P-8, P-9:** siguen abiertos según el Arquitecto. Ninguno bloquea este backend mínimo, pero P-1 y P-6 bloquearían cualquier lógica de servidor futura.
- **Pruebas:** no añado pruebas en `api/tests/`; eso corresponde al rol de Pruebas. No afirmo que el código funcione hasta que se ejecuten los comandos de verificación.

# Código y configuración

```text
# api/requirements.txt
fastapi==0.115.6
starlette==0.41.3
pydantic==2.10.3
uvicorn==0.32.1
```

```python
# api/app/__init__.py
```

```python
# api/app/config.py
"""Configuración leída de variables de entorno, con valores por defecto."""
import os

SERVICE_NAME: str = os.getenv("SERVICE_NAME", "merchant-qr-api")
API_VERSION: str = os.getenv("API_VERSION", "0.1.0")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
```

```python
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
```

```python
# api/app/services.py
"""Lógica de negocio. Aquí solo existe el estado del servicio."""
from app import config
from app.schemas import HealthResponse


def get_health() -> HealthResponse:
    return HealthResponse(status="ok", service=config.SERVICE_NAME)
```

```python
# api/app/routers/__init__.py
```

```python
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
```

```python
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
```

```python
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
```

# Verificación (todo NO EJECUTADO)

Instalación y comprobación de dependencias, desde `api/`:

```bash
# NO EJECUTADO
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip check
pip freeze | grep -iE '^(fastapi|starlette|pydantic|uvicorn)=='
```

Levantar el servicio, desde `api/`:

```bash
# NO EJECUTADO
uvicorn app.main:app --reload
```

**Caso válido: `GET /health`**

```bash
# NO EJECUTADO
curl -i http://127.0.0.1:8000/health
```

Esperado (NO EJECUTADO): `HTTP/1.1 200 OK`, con cuerpo `{"status":"ok","service":"merchant-qr-api"}`.

**Caso de error: ruta inexistente**

```bash
# NO EJECUTADO
curl -i http://127.0.0.1:8000/no-existe
```

Esperado (NO EJECUTADO): `HTTP/1.1 404 Not Found`, con cuerpo `{"code":"NOT_FOUND","message":"Recurso no encontrado."}`.

**Pruebas del repositorio**

```bash
# NO EJECUTADO
python tools/lab.py test api
```

Resultado: **NO EJECUTADO**. La persona que lo ejecute debe conservar la salida real. No se ha añadido ninguna prueba nueva en `api/tests/`, por lo que no hay cobertura propia de estos archivos.