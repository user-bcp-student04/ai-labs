# Pruebas de ReqFlow

Evidencia de pruebas por componente. Cada sección es de un componente; las de `auth` y `web` se documentan en sus pasos y no se tocan desde la sección `api`.

## web

Componente `web` (Angular). Hallazgo relacionado: H-WEB-01 en `HALLAZGOS.md`; decisión y alcance: `PLAN.md` (sección web). Los endpoints protegidos son `POST /auth/login` y `GET /api/tasks`; no se cambió su contrato.

### Caracterización y ejecución

- Fecha: 2026-11-03. Rama local `day1/prompting`. Comandos ejecutados desde la raíz salvo que se indique lo contrario.
- Antes de actualizar las dependencias, `python tools/lab.py test web` pasó con 6 pruebas; build exitoso. Esta línea base incluye las pruebas de caracterización agregadas para login y dashboard.
- Después de actualizar: `npm ci` (`web/`) terminó con exit 0; `python tools/lab.py test web` terminó con exit 0: 6 pruebas pasadas, cobertura y build completados.
- `npx tsc --noEmit -p tsconfig.json` (`web/`): exit 0.
- Los builds generan advertencias CommonJS para axios y lodash; no se suprimieron.

### Pruebas añadidas y cobertura

| Archivo | Pruebas | Comportamiento caracterizado |
|---|---:|---|
| `web/src/app/login/login.component.spec.ts` | 2 | Mezcla de preferencias; petición de login, persistencia de sesión, navegación y error. |
| `web/src/app/dashboard/dashboard.component.spec.ts` | 3 | Petición autenticada, exclusión de archivadas, redirección sin token y error de carga. |

Cobertura V8 de la ejecución final: 77,17% global; `login.component.ts` 90%; `dashboard.component.ts` 91,17%; `web/src/testing/test-helpers.ts` 100%. Los porcentajes por componente incluyen archivos completos; no se modificó código de producción.

### Dependencias y riesgos residuales

- `npm ls axios lodash --depth=0` (`web/`): `axios@0.34.0`, `lodash@4.18.1`.
- Consultas OSV para esas dos versiones: 0 advisories cada una.
- Baseline de `npm audit`: 43 vulnerabilidades (27 moderate, 10 high, 6 critical). Después de actualizar, `npm audit` terminó con exit 1 y reportó 41 (27 moderate, 8 high, 6 critical); no aparecen advisories para axios ni lodash.
- `npm audit --omit=dev` terminó con exit 1 y reportó 7 vulnerabilidades runtime (5 moderate, 2 high), en paquetes Angular y `follow-redirects`. Son residuales fuera del alcance aprobado; no se ejecutó `npm audit fix`.
- No se ejecutaron pruebas manuales ni integración Compose contra `auth`/`api`.

## api

Componente `api` (FastAPI + SQLite). Contrato de referencia: `docs/ENDPOINTS.md` (sección api). Hallazgos relacionados: `HALLAZGOS.md` (H-API-01 a H-API-14) y registro de ejecuciones de `PLAN.md`.

### Método y entorno

- Fecha: 2026-11-02. Rama local `day1/prompting`. Python 3.13.15 en `api/.venv`.
- Directorio de ejecución de las pruebas: `api/`. Comando equivalente desde la raíz: `python tools/lab.py test api`.
- Pruebas sin red real: base SQLite y directorio de subidas temporales (`tmp_path`), datos ficticios, y la llamada a `auth` se simula sustituyendo `urllib3.PoolManager.request`.
- Los tokens de prueba usan el formato legado y un valor de prueba aislado (`api/tests/conftest.py`). Cuando se resuelva H-API-02 habrá que regenerarlos.
- Los resultados de abajo son los realmente obtenidos; lo que no se ejecutó figura en "Pendientes" o "Propuestas".

### Archivos de prueba

| Archivo | Pruebas | Propósito |
|---|---|---|
| api/tests/test_api.py | 4 | Pruebas originales de la plantilla (sin cambios). |
| api/tests/test_characterization.py | 30 | Fijan el contrato observado (H-API-14). |
| api/tests/test_corrections_api.py | 36 | Pruebas de corrección por hallazgo (H-API-01, 03, 04, 07 a 13). |
| api/tests/test_units.py | 36 | Unidades de repositorio, servicios, configuración y token (H-API-01 a 04, 07, 09, 11). |
| api/tests/test_endpoints_contract.py | 59 | Nuevo en este paso: camino feliz, bordes y errores documentados por endpoint. |
| api/tests/conftest.py | — | Fixtures `client`, `auth_headers`, `upload_dir` y `build_token`. |

Total: 165 pruebas.

### Ejecuciones

| # | Comando (cwd) | Resultado | Código de salida | IDs |
|---|---|---|---|---|
| 1 | `python -m pytest tests/test_endpoints_contract.py -p no:warnings` (`api/`, con `.venv`) | 59 passed | no capturado | Endpoints de `docs/ENDPOINTS.md`; H-API-14 |
| 2 | `python -m pytest --cov=app --cov-report=term-missing --cov-report=json:<tmp> --cov-fail-under=85 -p no:warnings` (`api/`) | 165 passed; cobertura 100% (ver abajo) | 0 | Todos los H-API-NN con prueba; H-API-14 |
| 3 | `python tools/lab.py test api` (raíz) | 165 passed, 1 warning (deprecación de `TestClient` de Starlette, ajena al código); gate de 85% alcanzado; HTML en `api/htmlcov/index.html` | 0 | Todos; H-API-14 |
| 4 | `python -m pytest -p no:warnings` ×3 (`api/`) | 165 passed en cada ejecución | 0, 0, 0 | Estabilidad (H-API-12, H-API-14) |

Ejecuciones anteriores (código legado, refactor, revisión) están en "Registro de ejecuciones" de `PLAN.md`; entre ellas, sobre el código legado las pruebas de corrección dieron 33 fallos y 3 pasadas, resultado esperado de esa fase.

### Cobertura

- **Método**: `pytest-cov` con `--cov=app` y `branch = true` (de `api/pyproject.toml`); informe JSON de coverage.py. "Código modificado" = los archivos `.py` de `api/app/` que difieren de `main` (`git diff main --name-only -- api/app` más los archivos nuevos sin seguimiento, `git ls-files --others --exclude-standard -- api/app`), sin `__init__.py`. El cálculo suma líneas y ramas por archivo. Es cobertura por archivo completo, no por línea del diff.

| Medida | Numerador | Denominador | Resultado |
|---|---|---|---|
| Código modificado: sentencias | 293 | 293 | 100% |
| Código modificado: ramas | 20 | 20 | 100% |
| Código modificado: sentencias + ramas | 313 | 313 | 100,00% |
| Global (`--cov=app`, el gate de `tools/lab.py`): sentencias + ramas | 313 | 313 | 100,00% |

- Archivos modificados incluidos (8): `config.py`, `constants.py`, `main.py`, `repository.py`, `routes.py`, `schemas.py`, `security.py`, `services.py`, todos en `api/app/`. Detalle por archivo (sentencias; ramas): `config.py` 19/19; 2/2, `constants.py` 34/34; 0/0, `main.py` 26/26; 0/0, `repository.py` 51/51; 2/2, `routes.py` 31/31; 0/0, `schemas.py` 34/34; 0/0, `security.py` 27/27; 6/6, `services.py` 71/71; 10/10.
- La cobertura global coincide con la del código modificado porque todos los módulos de `app/` (salvo `__init__.py`, vacío) se crearon o cambiaron en este refactor; son medidas distintas que hoy dan el mismo valor.
- Límite: 100% de cobertura no demuestra que los asserts sean suficientes. Meta del laboratorio: 85% o más del código modificado (cumplida) y gate de toda la app en 85% (sin cambios de umbral).

### Casos por endpoint (endpoint | caso | tipo | resultado esperado)

La columna "Prueba" usa `archivo::función`, con `contract` = `test_endpoints_contract.py`, `char` = `test_characterization.py`, `corr` = `test_corrections_api.py` y `units` = `test_units.py`.

#### Errores comunes (todos los endpoints)

| Endpoint | Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|---|
| Los 5 | Sin header, token malformado, expirado o con secreto incorrecto | Error | 401 | `char::test_protected_routes_reject_invalid_tokens` (20 combinaciones) |
| Los 5 | Cuerpo del 401 | Error | `{"detail":"Invalid or expired token"}` | `contract::test_unauthorized_response_body_is_generic_on_every_endpoint` |
| Rutas definidas | Método no definido | Error | 405 `{"detail":"Method Not Allowed"}` | `contract::test_undefined_method_returns_405` |
| `GET /api/tasks` (representativo) | Error no controlado | Error | 500, texto `Internal Server Error`, sin detalle interno | `contract::test_unexpected_error_returns_generic_500` |

#### GET /api/tasks

| Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|
| Usuario con datos iniciales | Camino feliz | 200, 2 tareas con las 7 claves del contrato, orden por `id` | `char::test_lists_seeded_tasks_with_contract_keys` |
| Solo devuelve tareas propias | Camino feliz | Solo `owner == student`, orden por `id`, sin tareas de `trainer` | `contract::test_list_tasks_returns_only_own_tasks_in_id_order` |
| Usuario sin tareas | Borde | 200 `[]` | `contract::test_list_tasks_returns_empty_array_for_user_without_tasks` |
| `owner` vacío | Borde | Igual que sin parámetro | `contract::test_list_tasks_blank_owner_parameter_means_own_tasks` |
| `owner` igual al del token | Borde | 200 | `corr::test_explicit_own_owner_is_allowed` |
| Comilla en el usuario del token | Borde | 200 `[]`, la comilla es dato literal | `corr::test_username_with_quote_is_treated_as_literal_data` |
| Token ausente/inválido/expirado | Error 401 | Ver comunes | `char::test_protected_routes_reject_invalid_tokens[list_tasks]` |
| Un usuario no puede leer tareas de otro `owner` | Error 403 | 403 con `{"detail":"Access to another owner's data is not allowed"}`, sin datos de `trainer` | `contract::test_user_cannot_read_another_owners_tasks`, `corr::test_querying_another_owner_is_forbidden[/api/tasks]` |

#### POST /api/tasks

| Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|
| Datos válidos completos | Camino feliz | 201, tarea con `owner` del token; aparece en el listado | `contract::test_create_task_happy_path_persists_and_lists_the_task`, `char::test_create_task_returns_full_task` |
| Valores por defecto (solo `title`) | Camino feliz | `status=TODO`, `priority=MEDIUM`, `description=""` | `char::test_create_task_applies_defaults` |
| Cada `status` y `priority` documentado | Camino feliz | 201 y el valor guardado | `contract::test_create_task_accepts_every_documented_status`, `…_priority` |
| Payload vacío `{}` | Borde | 422 `missing` en `["body","title"]` | `contract::test_create_task_missing_title_error_body`, `corr::test_create_task_rejects_invalid_payload` |
| Longitud mínima y máxima (`title` 1 y 200, `description` 2000) | Borde | 201 | `contract::test_create_task_accepts_minimum_and_maximum_lengths` |
| Campos desconocidos y `owner` ajeno | Borde | Se ignoran; `owner` es el del token | `contract::test_create_task_ignores_unknown_fields`, `contract::test_create_task_cannot_assign_another_owner`, `corr::test_owner_in_body_is_ignored` |
| Comillas en `title`/`description` | Borde | 201, guardadas como texto literal | `corr::test_quotes_in_task_text_fields_are_stored_literally`, `units::test_repository_treats_quotes_as_literal_data` |
| Token ausente/inválido/expirado | Error 401 | Ver comunes | `char::test_protected_routes_reject_invalid_tokens[create_task]` |
| `title` ausente | Error 422 | Tipo `missing` | `contract::test_create_task_missing_title_error_body` |
| `status` o `priority` fuera de la lista | Error 422 | Tipo `enum` | `contract::test_create_task_invalid_status_error_body`, `…_invalid_priority_error_body` |
| `description` nulo | Error 422 | Tipo `string_type` | `contract::test_create_task_null_description_error_body` |
| `title` vacío, demasiado largo, `description` demasiado larga, tipo incorrecto | Error 422 | `string_too_short`, `string_too_long`, `string_type` | `contract::test_create_task_length_and_type_error_bodies` |
| JSON malformado | Error 422 | Tipo `json_invalid` | `contract::test_create_task_malformed_json_error_body` |

#### GET /api/summary

| Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|
| Usuario con datos iniciales | Camino feliz | `{"owner":"student","total":2,"byStatus":{"TODO":1,"IN_PROGRESS":1},"highPriorityOpen":1}` | `contract::test_summary_happy_path_for_seeded_user` |
| Combinación de estados y prioridades | Camino feliz | Conteos y `highPriorityOpen` correctos; claves en orden | `char::test_summary_counts_statuses_and_open_high_priority`, `units::test_is_high_priority_open` |
| Usuario sin tareas | Borde | `total 0`, `byStatus {}`, `highPriorityOpen 0` | `char::test_summary_for_user_without_tasks` |
| `owner` propio explícito o vacío | Borde | Igual que sin parámetro | `contract::test_summary_accepts_explicit_own_owner`, `contract::test_summary_blank_owner_parameter_means_own_summary` |
| Tareas de otros usuarios | Borde | No cuentan | `contract::test_summary_excludes_other_users_tasks` |
| Token ausente/inválido/expirado | Error 401 | Ver comunes | `char::test_protected_routes_reject_invalid_tokens[summary]` |
| Resumen de otro `owner` | Error 403 | 403 con el cuerpo documentado | `contract::test_summary_of_another_owner_is_forbidden`, `corr::test_querying_another_owner_is_forbidden[/api/summary]` |

#### POST /api/requirements

| Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|
| Archivo `.txt` válido | Camino feliz | 201, `owner`, `fileName`, `storedAt`, `size`; archivo guardado | `char::test_upload_keeps_contract_fields`, `contract::test_upload_accepts_each_allowed_extension` |
| `.txt`, `.md`, `.pdf` y mayúsculas | Camino feliz | 201 | `contract::test_upload_accepts_each_allowed_extension` |
| Archivo sin extensión | Borde | 415 `File extension not allowed`, nada guardado | `contract::test_upload_rejects_file_without_extension` |
| Límite de tamaño (1 MiB exacto y 1 MiB + 1 byte) | Borde | 201 y 413 sin guardar | `contract::test_upload_size_limit_boundary`, `corr::test_upload_accepts_file_at_the_size_limit` |
| Nombre con rutas, `\`, caracteres inseguros | Borde | Se normaliza y se guarda dentro del directorio de subidas | `corr::test_upload_strips_path_components`, `corr::test_upload_replaces_unsafe_characters`, `contract::test_upload_keeps_files_inside_upload_directory` |
| Mismo nombre dos veces | Borde | Se sobrescribe (comportamiento observado; ver Pendientes) | `char::test_upload_with_same_name_overwrites_previous_file` |
| `storedAt` | Borde | Solo el nombre, sin ruta del servidor | `corr::test_upload_does_not_expose_server_path` |
| Token ausente/inválido/expirado | Error 401 | Ver comunes | `char::test_protected_routes_reject_invalid_tokens[upload]` |
| Nombre vacío tras normalizar o de más de 100 caracteres | Error 400 | `{"detail":"Invalid file name"}` | `contract::test_upload_rejection_bodies`, `corr::test_upload_rejects_invalid_names` |
| Extensión no permitida | Error 415 | `{"detail":"File extension not allowed"}` | `contract::test_upload_rejection_bodies`, `corr::test_upload_rejects_disallowed_extension` |
| Más de 1 MiB | Error 413 | `{"detail":"File exceeds the maximum allowed size"}` | `contract::test_upload_size_limit_boundary`, `corr::test_upload_rejects_oversized_file` |
| Falta la parte `file` | Error 422 | Tipo `missing` en `["body","file"]` | `contract::test_upload_missing_file_part_error_body` |
| Nombre de archivo vacío | Error 422 | Tipo `value_error` en `["body","file"]` | `contract::test_upload_empty_filename_error_body` |

#### GET /api/backend-health

| Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|
| `auth` responde 200 | Camino feliz | 200 `{"requestedBy":"ana","status":200,"body":"{\"status\":\"UP\"}"}` | `contract::test_health_happy_path_reports_upstream_status_and_body`, `char::test_backend_health_reports_upstream_response` |
| `auth` responde 503 | Borde | HTTP 200, `status 503` y su cuerpo | `contract::test_health_forwards_upstream_error_status_with_http_200` |
| Cuerpo de más de 1000 caracteres | Borde | Se corta a 1000 | `contract::test_health_body_is_cut_at_the_documented_limit`, `corr::test_backend_health_limits_upstream_body` |
| URL y timeout definidos por el servidor | Borde | Usa `AUTH_HEALTH_URL` y 3,0 s; ignora parámetros del cliente | `contract::test_health_uses_server_configured_url_and_timeout`, `units::test_health_url_requires_http_scheme` |
| `auth` no disponible (`HTTPError` o `OSError`) | Borde | HTTP 200, `status 0`, `body "Backend unavailable"` | `contract::test_health_reports_unavailable_backend_with_http_200`, `corr::test_backend_health_hides_upstream_error_details` |
| Token ausente/inválido/expirado | Error 401 | Ver comunes | `char::test_protected_routes_reject_invalid_tokens[health]` |

Fuera de la tabla de endpoints, también hay pruebas de CORS (`corr::test_cors_*`), arranque e importación (`corr::test_importing_main_module_has_no_disk_side_effects`, `corr::test_startup_initializes_database_and_upload_dir`) y concurrencia (`corr::test_concurrent_requests_do_not_corrupt_state`).

### Fallos

Ninguno en las ejecuciones de este paso (4 de 4 con 0 fallos). No encontré ningún bug nuevo al escribir las pruebas; ninguna prueba se ajustó a un comportamiento defectuoso. Las observaciones sobre comportamientos dudosos se registran abajo, sin pruebas que los den por buenos.

### Pendientes

1. **H-API-02**: sin pruebas de firma, emisor y audiencia porque el JWT no está implementado ni acordado con `auth`. Las pruebas actuales dependen del token legado.
2. **H-API-04 (Pendiente en `HALLAZGOS.md`)**: sin prueba de que el servidor rechace un cuerpo grande antes de recibirlo (hoy no lo hace) ni del aislamiento de archivos por usuario (hoy un usuario puede sobrescribir el de otro; solo existe la prueba que fija la sobrescritura como comportamiento observado, no como requisito).
3. **H-API-05 (Pendiente)**: no hay prueba pytest; se verifica con OSV y `pip check`.
4. Integración con `web` y `auth` (Compose): no ejecutada.
5. Cobertura del diff por línea: no medida; se midió por archivo completo.

### Observaciones para reportar aparte (sin test que las dé por buenas)

- `title` con solo espacios se acepta con 201 (`docs/ENDPOINTS.md`, pregunta 3).
- El token sin el prefijo `Bearer ` también se acepta (`api/app/security.py`, `removeprefix`; pregunta 2). No hay prueba que lo exija ni que lo permita.
- La respuesta 422 repite el valor enviado en `input`; si algún campo llevara datos sensibles se reflejaría en la respuesta (comportamiento por defecto de FastAPI; no probado como requisito).

### Pruebas propuestas (no ejecutadas)

- Tras resolver H-API-02: token firmado válido, firma alterada, `alg` distinto, emisor y audiencia incorrectos, expiración.
- Tras decidir la política de archivos repetidos: aislamiento por usuario o rechazo de nombre repetido; prueba de límite de cuerpo en el servidor o proxy.
- Decisión sobre títulos de solo espacios: prueba que rechace o acepte según se acuerde.
- Decisión sobre el prefijo `Bearer`.
- Archivo de 0 bytes, nombres Unicode y nombres reservados de Windows (`CON.txt`).
- Prueba de contrato contra `/openapi.json` para detectar cambios no documentados en `docs/ENDPOINTS.md`.
- Prueba de integración con `web` y `auth` en Compose.
- Pruebas de mutación para validar la calidad de los asserts más allá de la cobertura.

### Código de las pruebas nuevas

`api/tests/test_endpoints_contract.py` (59 pruebas). Los demás archivos de la tabla "Archivos de prueba" están en el repositorio.

```python
"""Pruebas por endpoint según docs/ENDPOINTS.md (sección api).

Cada endpoint cubre camino feliz, casos borde y cada respuesta de error documentada.
Sin red real: la llamada a `auth` se simula con `urllib3.PoolManager.request`.
"""

import types
from collections.abc import Callable
from pathlib import Path

import pytest
import urllib3
from fastapi.testclient import TestClient

from app.repository import TaskRepository
from test_characterization import PROTECTED_REQUESTS

Headers = Callable[..., dict[str, str]]

UNAUTHORIZED_BODY = {"detail": "Invalid or expired token"}
FORBIDDEN_BODY = {"detail": "Access to another owner's data is not allowed"}
MAX_UPLOAD_BYTES = 1024 * 1024
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
HEALTH_BODY_LIMIT = 1000
CONFIGURED_HEALTH_URL = "http://auth.test:8080/q/health"
HEALTH_TIMEOUT_SECONDS = 3.0


def stub_upstream(monkeypatch: pytest.MonkeyPatch, status: int, data: bytes) -> list[tuple]:
    calls: list[tuple] = []

    def fake_request(self: object, method: str, url: str, **kwargs: object) -> types.SimpleNamespace:
        calls.append((method, url, kwargs))
        return types.SimpleNamespace(status=status, data=data)

    monkeypatch.setattr(urllib3.PoolManager, "request", fake_request)
    return calls


def create_task(client: TestClient, headers: dict[str, str], **fields: object) -> dict:
    response = client.post("/api/tasks", headers=headers, json=fields)
    assert response.status_code == 201
    return response.json()


def upload(client: TestClient, headers: dict[str, str], name: str, content: bytes = b"x"):
    return client.post("/api/requirements", headers=headers, files={"file": (name, content, "text/plain")})


# --- Errores comunes (todos los endpoints) ---------------------------------------------------


@pytest.mark.parametrize("request_spec", PROTECTED_REQUESTS.values(), ids=PROTECTED_REQUESTS.keys())
def test_unauthorized_response_body_is_generic_on_every_endpoint(
    client: TestClient, request_spec: tuple
) -> None:
    method, path, kwargs = request_spec

    response = client.request(method, path, **kwargs)

    assert (response.status_code, response.json()) == (401, UNAUTHORIZED_BODY)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("delete", "/api/tasks"),
        ("put", "/api/tasks"),
        ("post", "/api/summary"),
        ("get", "/api/requirements"),
        ("post", "/api/backend-health"),
    ],
)
def test_undefined_method_returns_405(client: TestClient, auth_headers: Headers, method: str, path: str) -> None:
    response = client.request(method, path, headers=auth_headers())

    assert (response.status_code, response.json()) == (405, {"detail": "Method Not Allowed"})


def test_unexpected_error_returns_generic_500(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(self: object, owner: str) -> None:
        raise RuntimeError("db exploded")

    monkeypatch.setattr(TaskRepository, "list_by_owner", explode)

    response = client.get("/api/tasks", headers=auth_headers())

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert "db exploded" not in response.text


# --- GET /api/tasks -------------------------------------------------------------------------


def test_list_tasks_returns_only_own_tasks_in_id_order(client: TestClient, auth_headers: Headers) -> None:
    create_task(client, auth_headers("trainer"), title="Trainer secret")
    create_task(client, auth_headers(), title="Mine")

    tasks = client.get("/api/tasks", headers=auth_headers()).json()

    assert [task["title"] for task in tasks] == ["Refactor login", "Review API", "Mine"]
    assert {task["owner"] for task in tasks} == {"student"}
    assert [task["id"] for task in tasks] == sorted(task["id"] for task in tasks)


def test_list_tasks_returns_empty_array_for_user_without_tasks(client: TestClient, auth_headers: Headers) -> None:
    response = client.get("/api/tasks", headers=auth_headers("nobody"))

    assert (response.status_code, response.json()) == (200, [])


def test_list_tasks_blank_owner_parameter_means_own_tasks(client: TestClient, auth_headers: Headers) -> None:
    without_param = client.get("/api/tasks", headers=auth_headers()).json()

    with_blank_param = client.get("/api/tasks", headers=auth_headers(), params={"owner": ""})

    assert (with_blank_param.status_code, with_blank_param.json()) == (200, without_param)


def test_user_cannot_read_another_owners_tasks(client: TestClient, auth_headers: Headers) -> None:
    create_task(client, auth_headers("trainer"), title="Trainer secret")

    forbidden = client.get("/api/tasks", headers=auth_headers(), params={"owner": "trainer"})
    own = client.get("/api/tasks", headers=auth_headers())

    assert (forbidden.status_code, forbidden.json()) == (403, FORBIDDEN_BODY)
    assert "Trainer" not in forbidden.text
    assert "Trainer secret" not in own.text


# --- POST /api/tasks ------------------------------------------------------------------------


def test_create_task_happy_path_persists_and_lists_the_task(client: TestClient, auth_headers: Headers) -> None:
    created = create_task(
        client, auth_headers(), title="Write docs", description="Document", status="IN_PROGRESS", priority="HIGH"
    )

    listed = client.get("/api/tasks", headers=auth_headers()).json()

    assert created in listed
    assert (created["owner"], created["status"], created["priority"]) == ("student", "IN_PROGRESS", "HIGH")


@pytest.mark.parametrize("status", ["TODO", "IN_PROGRESS", "DONE", "ARCHIVED"])
def test_create_task_accepts_every_documented_status(client: TestClient, auth_headers: Headers, status: str) -> None:
    assert create_task(client, auth_headers(), title="t", status=status)["status"] == status


@pytest.mark.parametrize("priority", ["HIGH", "MEDIUM", "LOW"])
def test_create_task_accepts_every_documented_priority(
    client: TestClient, auth_headers: Headers, priority: str
) -> None:
    assert create_task(client, auth_headers(), title="t", priority=priority)["priority"] == priority


def test_create_task_accepts_minimum_and_maximum_lengths(client: TestClient, auth_headers: Headers) -> None:
    create_task(client, auth_headers(), title="a")
    longest = create_task(
        client, auth_headers(), title="t" * MAX_TITLE_LENGTH, description="d" * MAX_DESCRIPTION_LENGTH
    )

    assert (len(longest["title"]), len(longest["description"])) == (MAX_TITLE_LENGTH, MAX_DESCRIPTION_LENGTH)


def test_create_task_ignores_unknown_fields(client: TestClient, auth_headers: Headers) -> None:
    created = create_task(client, auth_headers(), title="t", owner="trainer", unexpected="value")

    assert "unexpected" not in created
    assert created["owner"] == "student"


def test_create_task_missing_title_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert (error["type"], error["loc"], error["msg"]) == ("missing", ["body", "title"], "Field required")


def test_create_task_invalid_status_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "t", "status": "BOGUS"})

    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["type"], error["loc"], error["input"]) == ("enum", ["body", "status"], "BOGUS")


def test_create_task_invalid_priority_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "t", "priority": "URGENT"})

    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["type"], error["loc"]) == ("enum", ["body", "priority"])


def test_create_task_null_description_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json={"title": "t", "description": None})

    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["type"], error["loc"]) == ("string_type", ["body", "description"])


@pytest.mark.parametrize(
    ("payload", "error_type"),
    [
        ({"title": ""}, "string_too_short"),
        ({"title": "t" * (MAX_TITLE_LENGTH + 1)}, "string_too_long"),
        ({"title": "t", "description": "d" * (MAX_DESCRIPTION_LENGTH + 1)}, "string_too_long"),
        ({"title": 123}, "string_type"),
    ],
)
def test_create_task_length_and_type_error_bodies(
    client: TestClient, auth_headers: Headers, payload: dict, error_type: str
) -> None:
    response = client.post("/api/tasks", headers=auth_headers(), json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == error_type


def test_create_task_malformed_json_error_body(client: TestClient, auth_headers: Headers) -> None:
    headers = {**auth_headers(), "Content-Type": "application/json"}

    response = client.post("/api/tasks", headers=headers, content="nope")

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"


def test_create_task_cannot_assign_another_owner(client: TestClient, auth_headers: Headers) -> None:
    create_task(client, auth_headers(), title="Planted", owner="trainer")

    trainer_titles = [task["title"] for task in client.get("/api/tasks", headers=auth_headers("trainer")).json()]

    assert trainer_titles == ["Trainer notes"]


# --- GET /api/summary -----------------------------------------------------------------------


def test_summary_happy_path_for_seeded_user(client: TestClient, auth_headers: Headers) -> None:
    response = client.get("/api/summary", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {
        "owner": "student",
        "total": 2,
        "byStatus": {"TODO": 1, "IN_PROGRESS": 1},
        "highPriorityOpen": 1,
    }


def test_summary_accepts_explicit_own_owner(client: TestClient, auth_headers: Headers) -> None:
    implicit = client.get("/api/summary", headers=auth_headers()).json()

    explicit = client.get("/api/summary", headers=auth_headers(), params={"owner": "student"})

    assert (explicit.status_code, explicit.json()) == (200, implicit)


def test_summary_blank_owner_parameter_means_own_summary(client: TestClient, auth_headers: Headers) -> None:
    response = client.get("/api/summary", headers=auth_headers(), params={"owner": ""})

    assert response.json()["owner"] == "student"


def test_summary_excludes_other_users_tasks(client: TestClient, auth_headers: Headers) -> None:
    create_task(client, auth_headers("trainer"), title="x", priority="HIGH")

    summary = client.get("/api/summary", headers=auth_headers()).json()

    assert (summary["total"], summary["highPriorityOpen"]) == (2, 1)


def test_summary_of_another_owner_is_forbidden(client: TestClient, auth_headers: Headers) -> None:
    response = client.get("/api/summary", headers=auth_headers(), params={"owner": "trainer"})

    assert (response.status_code, response.json()) == (403, FORBIDDEN_BODY)


# --- POST /api/requirements -----------------------------------------------------------------


@pytest.mark.parametrize("file_name", ["notes.txt", "notes.md", "notes.pdf", "NOTES.TXT"])
def test_upload_accepts_each_allowed_extension(
    client: TestClient, auth_headers: Headers, upload_dir: Path, file_name: str
) -> None:
    response = upload(client, auth_headers(), file_name, b"abc")

    assert (response.status_code, response.json()) == (
        201,
        {"owner": "student", "fileName": file_name, "storedAt": file_name, "size": 3},
    )
    assert (upload_dir / file_name).read_bytes() == b"abc"


def test_upload_rejects_file_without_extension(client: TestClient, auth_headers: Headers, upload_dir: Path) -> None:
    response = upload(client, auth_headers(), "README")

    assert (response.status_code, response.json()) == (415, {"detail": "File extension not allowed"})
    assert not (upload_dir / "README").exists()


def test_upload_size_limit_boundary(client: TestClient, auth_headers: Headers, upload_dir: Path) -> None:
    at_limit = upload(client, auth_headers(), "at-limit.txt", b"x" * MAX_UPLOAD_BYTES)
    over_limit = upload(client, auth_headers(), "over-limit.txt", b"x" * (MAX_UPLOAD_BYTES + 1))

    assert at_limit.status_code == 201
    assert (over_limit.status_code, over_limit.json()) == (413, {"detail": "File exceeds the maximum allowed size"})
    assert not (upload_dir / "over-limit.txt").exists()


@pytest.mark.parametrize(
    ("file_name", "expected_status", "expected_detail"),
    [
        ("..", 400, "Invalid file name"),
        ("a" * 101 + ".txt", 400, "Invalid file name"),
        ("run.exe", 415, "File extension not allowed"),
        ("archive.tar.gz", 415, "File extension not allowed"),
    ],
)
def test_upload_rejection_bodies(
    client: TestClient, auth_headers: Headers, file_name: str, expected_status: int, expected_detail: str
) -> None:
    response = upload(client, auth_headers(), file_name)

    assert (response.status_code, response.json()) == (expected_status, {"detail": expected_detail})


def test_upload_missing_file_part_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = client.post("/api/requirements", headers=auth_headers())

    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["type"], error["loc"]) == ("missing", ["body", "file"])


def test_upload_empty_filename_error_body(client: TestClient, auth_headers: Headers) -> None:
    response = upload(client, auth_headers(), "")

    error = response.json()["detail"][0]
    assert response.status_code == 422
    assert (error["type"], error["loc"]) == ("value_error", ["body", "file"])


def test_upload_keeps_files_inside_upload_directory(
    client: TestClient, auth_headers: Headers, upload_dir: Path
) -> None:
    upload(client, auth_headers(), "../../outside.txt")

    assert sorted(path.name for path in upload_dir.iterdir()) == ["outside.txt"]
    assert not (upload_dir.parent / "outside.txt").exists()


# --- GET /api/backend-health ----------------------------------------------------------------


def test_health_happy_path_reports_upstream_status_and_body(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    stub_upstream(monkeypatch, 200, b'{"status":"UP"}')

    response = client.get("/api/backend-health", headers=auth_headers("ana"))

    assert (response.status_code, response.json()) == (
        200,
        {"requestedBy": "ana", "status": 200, "body": '{"status":"UP"}'},
    )


def test_health_forwards_upstream_error_status_with_http_200(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    stub_upstream(monkeypatch, 503, b"down for maintenance")

    response = client.get("/api/backend-health", headers=auth_headers())

    assert (response.status_code, response.json()["status"], response.json()["body"]) == (
        200,
        503,
        "down for maintenance",
    )


def test_health_body_is_cut_at_the_documented_limit(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    stub_upstream(monkeypatch, 200, b"x" * (HEALTH_BODY_LIMIT + 500))

    body = client.get("/api/backend-health", headers=auth_headers()).json()["body"]

    assert body == "x" * HEALTH_BODY_LIMIT


@pytest.mark.parametrize("failure", [urllib3.exceptions.HTTPError("refused"), ConnectionRefusedError("refused")])
def test_health_reports_unavailable_backend_with_http_200(
    client: TestClient, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    def fail(self: object, method: str, url: str, **kwargs: object) -> None:
        raise failure

    monkeypatch.setattr(urllib3.PoolManager, "request", fail)

    response = client.get("/api/backend-health", headers=auth_headers())

    assert (response.status_code, response.json()) == (
        200,
        {"requestedBy": "student", "status": 0, "body": "Backend unavailable"},
    )


def test_health_uses_server_configured_url_and_timeout(
    tmp_path: Path, auth_headers: Headers, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.main import create_app

    monkeypatch.setenv("AUTH_HEALTH_URL", CONFIGURED_HEALTH_URL)
    calls = stub_upstream(monkeypatch, 200, b"UP")
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    with TestClient(app) as configured_client:
        configured_client.get("/api/backend-health", headers=auth_headers(), params={"url": "http://evil.test"})

    assert [(method, url, kwargs["timeout"]) for method, url, kwargs in calls] == [
        ("GET", CONFIGURED_HEALTH_URL, HEALTH_TIMEOUT_SECONDS)
    ]
```

## auth

Componente `auth` (Quarkus + SQLite). Hallazgo H-AUTH-01 (`HALLAZGOS.md`); Issue #23; cambio OpenSpec `auth-login-parameterized-queries`. Rama local `feature/h-auth-01`, sin push. Contrato de `POST /auth/login` sin cambios.

### Entorno

- Comando oficial: `python tools/lab.py test auth` (raíz), que ejecuta `mvn verify` en `auth/`.
- Quarkus usa el puerto de prueba 8081 por defecto y en esta máquina está ocupado por el servidor MCP local. Se movió con `QUARKUS_HTTP_TEST_PORT=18081` en `auth/.env` (ignorado por git; no es parte del cambio).

### Pruebas (`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`)

| Prueba | Requisito de la spec que protege | Antes de corregir | Después |
|---|---|---|---|
| `logsInWithWorkshopUser` (existente) | Credenciales válidas: `student` | pasa | pasa |
| `keepsLoginResponseContract` | Credenciales válidas: forma del 200 (`token`, `expiresIn` 3600, `user.*`, `debug`) | pasa | pasa |
| `logsInWithTrainerUser` | Credenciales válidas: `trainer` | pasa | pasa |
| `rejectsWrongPassword` | Credenciales inválidas: 401 sin `token` | pasa | pasa |
| `rejectsUnknownUser` | Credenciales inválidas: 401 sin `token` | pasa | pasa |
| `rejectsEmptyUsername` | Validación preservada: 400 `Username is required` | pasa | pasa |
| `rejectsEmptyPassword` | Validación preservada: 400 `Password is required` | pasa | pasa |
| `rejectsSqlInjectionInUsername` | Valores no alteran la consulta: `' OR '1'='1` en usuario | pasa (regresión) | pasa |
| `rejectsSqlInjectionInPassword` | Valores no alteran la consulta: `' OR '1'='1` en contraseña | **falla** (200) | pasa |
| `rejectsSqlCommentInjectionInUsername` | Valores no alteran la consulta: `student'--` | **falla** (200) | pasa |

`rejectsSqlInjectionInUsername` pasa con el código original porque `AND` precede a `OR` y la condición `username='' OR '1'='1' AND password='...'` resulta falsa; se conserva como regresión (ver `design.md`). Las pruebas de 401 no verifican `message`.

### Ejecuciones

| # | Comando | Código | Resultado |
|---|---|---|---|
| 1 | `python tools/lab.py test auth` (raíz, puerto 8081 ocupado) | 1 | `Port already bound: 8081`; las pruebas no arrancaron |
| 2 | `python tools/lab.py test auth` (con `QUARKUS_HTTP_TEST_PORT=18081`, código original, 6 pruebas) | 0 | 6 passed |
| 3 | Ídem, con las 3 pruebas de inyección, código original | 1 | 9 ejecutadas, 2 fallos (200 en lugar de 401) |
| 4 | Ídem, código original, 10 pruebas (con `keepsLoginResponseContract`) | 1 | 10 ejecutadas, mismos 2 fallos |
| 5 | Ídem, con la corrección | 0 | 10 passed, `BUILD SUCCESS` |

### Cobertura (JaCoCo, `auth/target/site/jacoco/jacoco.xml`)

Código modificado: `LegacyDatabase.findByCredentials` y su constante SQL.

| Medida | Cubierto / total | % |
|---|---|---|
| Instrucciones | 54 / 57 | 94,7% |
| Líneas | 11 / 12 | 91,7% |
| Ramas | 5 / 8 | 62,5% |
| Clase `LegacyDatabase` (instrucciones) | 92 / 98 | 93,9% |

La línea sin cubrir es el `catch` (`printStackTrace`); no se forzó con cambios de producción. Las ramas sin cubrir son el `catch` y las ramas sintéticas del `try-with-resources` anidado. La meta de 85% se cumple en instrucciones y líneas, no en ramas.

### Pendientes

- Revisión humana del diff antes de cualquier integración.
- Sin prueba del 500 ni del fallo de acceso a la base de datos (fuera de alcance).
- Sin integración con `web`/`api` (Compose).
