# Plan de corrección de ReqFlow

Propuesta de corrección por hallazgo. Cada apartado enlaza con su fila de `HALLAZGOS.md`. Este plan no modifica código; el estado de cada hallazgo lo actualiza el paso de refactor con evidencia real.

## api

### Base de partida

- Entradas leídas: `HALLAZGOS.md` (H-API-01 a H-API-14, todos `Pendiente`), `docs/GOOD_PRACTICES.md` (sección api), `RETO.md`, `AGENTS.md` (Clean Code de api) y `api/app/main.py`, `api/tests/test_api.py`, `api/requirements.txt`.
- `docs/ENDPOINTS.md` **no existe**: se conserva el comportamiento observado descrito en `HALLAZGOS.md` (sección "Contrato observado"). No se cambian rutas, métodos, nombres de campos ni códigos de éxito (200/201). Los cambios que alteran comportamiento observado se marcan como **[Decisión]** y requieren aprobación humana antes de implementarse; no hay aprobación registrada.
- `docs/TESTING.md` no existe; los resultados de las pruebas se registrarán allí en el paso correspondiente, ligados a componente e IDs.
- Dependencias nuevas: ninguna. Pydantic (`pydantic==2.13.4`) ya está en `api/requirements.txt`; la verificación de token usa solo la biblioteca estándar (ver H-API-02).
- Convenciones fuera de `docs/GOOD_PRACTICES.md` (CORS, límites de subida, constantes) se proponen como **propuesta sujeta a aprobación**, no como convención establecida.

### Estructura objetivo (ruta → servicio → repositorio)

Se crea dentro de `api/app/`; `main.py` queda solo con `create_app` y el cableado.

| Archivo | Responsabilidad |
|---|---|
| api/app/config.py | Lee variables de entorno (`WORKSHOP_DB_PATH`, `WORKSHOP_UPLOAD_DIR`, `AUTH_HEALTH_URL` ya existentes; nuevas: secreto/emisor/audiencia del token, orígenes CORS) y expone constantes con nombre. |
| api/app/constants.py | Valores de dominio: estados, prioridades, estados "cerrados", límites de subida, extensiones permitidas, timeout de health. |
| api/app/schemas.py | Modelos Pydantic de request y response. |
| api/app/security.py | Verificación del token y dependencia `current_identity`. |
| api/app/repository.py | `TaskRepository`: único lugar con SQL, siempre parametrizado. |
| api/app/services.py | `TaskService` (reglas, resumen), `RequirementUploadService`, `BackendHealthService`. |
| api/app/routes.py | Routers FastAPI delgados: validan, llaman al servicio, devuelven el modelo. |

### Orden de ejecución propuesto

1. H-API-14: pruebas de caracterización del comportamiento actual (verdes antes de tocar código). Las pruebas que codifican un comportamiento inseguro se marcan para invertirse en el hallazgo que lo corrige.
2. H-API-05: actualizar dependencias (cambio aislado en `requirements.txt`) y volver a correr la suite.
3. H-API-06 + H-API-13 + H-API-12 + H-API-07: separar capas sin cambiar comportamiento.
4. H-API-01, H-API-03, H-API-10: repositorio parametrizado, autorización por identidad y modelos.
5. H-API-02 (coordinado con `auth`), H-API-04, H-API-08, H-API-09, H-API-11.

Cobertura: meta de 85% o más del código modificado; el gate de 85% de toda la app se conserva. No se bajan umbrales.

---

### H-API-01 — SQL concatenado con entrada del cliente

- **Hallazgo**: `HALLAZGOS.md` H-API-01 (Vulnerabilidad, alta).
- **Problema**: `owner` (query) y `title`, `description`, `status`, `priority`, `owner` (body) se concatenan en el SQL (api/app/main.py:70, 84, 93). Una comilla altera la consulta.
- **Cambio propuesto**: `TaskRepository` con `list_by_owner(owner)`, `insert(new_task)`, `get_by_id(id)` y `statuses_and_priorities_by_owner(owner)`, todos con placeholders `?` y tupla de parámetros. Ninguna ruta ni servicio construye SQL. El SQL se define como constantes de módulo con nombre. El SELECT por `lastrowid` (main.py:87) también se parametriza por uniformidad. El esquema y el seed se mueven a un método `initialize_schema()` del repositorio sin cambiar sus datos.
- **Contrato**: las respuestas no cambian; una comilla en cualquier campo se almacena y devuelve como dato literal.
- **Archivos a tocar**: api/app/repository.py (nuevo), api/app/services.py (nuevo), api/app/routes.py (nuevo), api/app/main.py, api/tests/test_repository.py (nuevo), api/tests/test_api.py.
- **Prueba de caracterización previa** (api/tests/test_characterization.py, DB temporal y datos ficticios):
  - Crear tarea con comilla simple en `title` y `description` (por ejemplo `O'Brien`): hoy es hipótesis de fallo/alteración; la prueba registra el comportamiento actual y, tras el cambio, afirma que `201` y que el valor devuelto es idéntico al enviado.
  - `GET /api/tasks` con `owner` que contiene una comilla: tras el cambio devuelve `200` y lista vacía (o solo las del propio usuario), nunca filas de otros owners.
  - Con token inválido: `401` en las tres rutas.

### H-API-02 — Token Base64 con secreto embebido

- **Hallazgo**: `HALLAZGOS.md` H-API-02 (Vulnerabilidad, alta).
- **Problema**: el token es `base64(usuario|rol|exp|secreto)` y el secreto está en el código (api/app/main.py:14, 19-24); no hay firma, emisor ni audiencia.
- **Cambio propuesto**: `security.py` con una clase `TokenVerifier` que verifica un JWT HS256 usando solo la biblioteca estándar (`hmac`, `hashlib`, `base64`, `json`), sin dependencia nueva. Verifica, en este orden y con retorno anticipado: formato de 3 segmentos, algoritmo esperado (rechaza `none` y cualquier otro), firma con `hmac.compare_digest`, `exp` vigente, `iss` y `aud` iguales a los configurados; los claims `sub` (usuario) y `role` se mapean a la identidad `{username, role}`. Secreto, emisor y audiencia vienen de variables de entorno (`config.py`), sin valor por defecto de producción; las pruebas usan valores aislados de prueba. Constantes con nombre para el prefijo `Bearer`, los nombres de claims y el algoritmo. Todo fallo lanza `HTTPException(401)` con mensaje genérico (ver H-API-08).
- **Alternativa a evaluar**: PyJWT, solo si se justifica el costo de una dependencia nueva; la propuesta base no la necesita.
- **[Decisión] / coordinación**: el formato actual lo emite el componente `auth`, que este plan no puede leer ni cambiar. Hay que acordar con `auth` el contrato del JWT (algoritmo, secreto compartido o clave, `iss`, `aud`, nombres de claims, expiración) antes de implementar. Hasta entonces el flujo extremo a extremo con `web`/`auth` seguiría roto. No se propone aceptar el formato Base64 como respaldo: conservaría la vulnerabilidad. Si se necesitara un periodo de transición, requiere aprobación explícita y fecha de retiro.
- **Contrato**: header `Authorization: Bearer <token>`; `401` ante token ausente o inválido; la identidad sigue siendo `{username, role}`.
- **Archivos a tocar**: api/app/security.py (nuevo), api/app/config.py (nuevo), api/app/main.py, api/tests/conftest.py (fábrica de tokens firmados para pruebas), api/tests/test_security.py (nuevo), api/tests/test_api.py (helper `token`, que hoy forja Base64). Documentar las variables nuevas en README de api solo si el equipo lo aprueba.
- **Prueba de caracterización previa**: sobre el comportamiento actual, tokens ausente, vacío, malformado, expirado y con secreto incorrecto devuelven `401`; un token válido devuelve `200`. Tras el cambio se agregan pruebas de firma alterada, `alg=none`, `iss` y `aud` incorrectos y expirado, todas con `401` y detalle genérico.

### H-API-03 — `owner` controlado por el cliente

- **Hallazgo**: `HALLAZGOS.md` H-API-03 (Vulnerabilidad, alta).
- **Problema**: `owner` de query y de body prevalece sobre la identidad (api/app/main.py:69, 83, 92); el `role` no se usa (main.py:24).
- **Cambio propuesto**: según `docs/GOOD_PRACTICES.md`, las consultas usan siempre `identity.username` del token verificado. `list_tasks` y `summary` filtran por esa identidad; `create_task` fija `owner = identity.username` e ignora el `owner` del body. Un helper único `resolve_owner(identity, requested_owner)` evita repetir la lógica en tres rutas.
- **[Decisión]**: qué hacer cuando el cliente envía un `owner` distinto al suyo. Opciones: (a) `403`, explícito; (b) ignorarlo en silencio y devolver los datos propios. Se recomienda (a), pero cambia el comportamiento observado y requiere aprobación. Si el negocio necesita que un rol (por ejemplo `trainer`) vea tareas ajenas, no está definido en `GOOD_PRACTICES.md` ni en el contrato: se deja como pendiente y no se inventa regla de roles.
- **Contrato**: sin `owner` (uso normal del frontend), las respuestas son idénticas a las actuales.
- **Archivos a tocar**: api/app/services.py, api/app/routes.py, api/tests/test_authorization.py (nuevo).
- **Prueba de caracterización previa**: con dos usuarios ficticios (`student`, `trainer`; el seed ya tiene tareas de ambos), registrar que hoy `student` puede leer las de `trainer` con `?owner=trainer` (comportamiento inseguro, a invertir); sin `owner`, `student` ve solo las suyas (2). Tras el cambio: `?owner=trainer` según la decisión aprobada, y `POST` con `owner` ajeno crea la tarea a nombre del usuario autenticado.

### H-API-04 — Carga de archivos insegura

- **Hallazgo**: `HALLAZGOS.md` H-API-04 (Vulnerabilidad, alta).
- **Problema**: se usa `file.filename` tal cual, se lee todo en memoria y se escribe sin límites (api/app/main.py:109-112); se expone la ruta de almacenamiento.
- **Cambio propuesto**: `RequirementUploadService` con funciones pequeñas: `sanitize_filename` (quita componentes de ruta con `PurePath(...).name`, descarta vacíos, caracteres de control y puntos iniciales, y limita la longitud), `validate_extension` (lista permitida en `constants.py`), `read_with_limit` (lee por bloques y aborta al pasar el máximo), `resolve_target` (comprueba que la ruta resuelta sigue dentro del directorio de subidas). Retornos anticipados con `HTTPException`: `400` nombre inválido, `415` extensión no permitida, `413` tamaño excedido.
- **[Decisión]**: extensiones permitidas y tamaño máximo (propuesta inicial: `.txt`, `.md`, `.pdf`; 1 MiB, ambos como constantes con nombre); política ante nombre repetido (hoy se sobrescribe); y qué valor devolver en `storedAt` (hoy la ruta con el directorio del servidor). Se recomienda mantener el campo para no romper el contrato, pero devolver solo el nombre almacenado. Confirmar que `web` no consume `storedAt` (no se puede leer ese componente desde este plan).
- **Contrato**: `POST /api/requirements` mantiene `201` y `{owner, fileName, storedAt, size}`; la subida de `requirements.txt` sigue guardándose en el directorio de subidas.
- **Archivos a tocar**: api/app/services.py, api/app/routes.py, api/app/constants.py, api/tests/test_uploads.py (nuevo).
- **Prueba de caracterización previa**: (1) subida válida de `requirements.txt` guarda el archivo y devuelve `201` y `size` correcto (ya existe); (2) en directorio temporal, registrar cómo se comporta hoy un nombre con separadores de ruta usando datos ficticios (hipótesis sin ejecutar: se aceptaría); tras el cambio se afirma que nunca se escribe fuera del directorio de subidas, que una extensión no permitida da `415` y que un archivo mayor al límite da `413` sin escribir nada.

### H-API-05 — Dependencias con CVEs

- **Hallazgo**: `HALLAZGOS.md` H-API-05 (Vulnerabilidad, media).
- **Problema**: `urllib3==2.5.0` y `python-multipart==0.0.21` (api/requirements.txt:4-5) tienen advisories en OSV.
- **Cambio propuesto**: según OSV, las correcciones están en `urllib3` 2.6.0 / 2.6.3 / 2.7.0 / 2.8.0 y en `python-multipart` 0.0.22 / 0.0.26 / 0.0.27 / 0.0.30 / 0.0.31, según el advisory. Para cerrarlos todos se propone subir a la versión estable más reciente verificada (índice público: `urllib3` 2.8.0 y `python-multipart` 0.0.33), fijándola con `==` como el resto del archivo, y volver a consultar OSV con la versión elegida. Verificar compatibilidad con `fastapi==0.128.2` y `uvicorn[standard]==0.48.0` con la suite completa y `pip check` en `api/.venv`. Dependencia nueva: ninguna. Si alguna versión rompe compatibilidad, se registra el advisory residual en `HALLAZGOS.md` en vez de silenciarlo.
- **Archivos a tocar**: api/requirements.txt. (`requirements-dev.txt` solo si `pip check` lo exige.)
- **Prueba de caracterización previa**: ejecutar la suite actual (4 pruebas) y registrar el resultado antes del cambio; repetirla después. Repetir las pruebas de subida (H-API-04) y `backend-health` (H-API-11), que ejercitan ambas bibliotecas.

### H-API-06 — Arquitectura monolítica

- **Hallazgo**: `HALLAZGOS.md` H-API-06 (Refactor, media).
- **Problema**: `create_app` mezcla conexión, esquema, CORS, rutas, SQL y serialización (api/app/main.py:29-127).
- **Cambio propuesto**: la estructura de la tabla "Estructura objetivo". Rutas delgadas (`routes.py`) que reciben dependencias (servicio, identidad); servicios con las reglas; repositorio con SQL. Se hace como primer paso sin cambio de comportamiento, para que H-API-01 y H-API-03 sean cambios pequeños y revisables. Un cambio por commit/PR: primero la extracción, luego cada corrección.
- **Archivos a tocar**: los de la tabla de estructura, api/app/main.py, api/tests/.
- **Prueba de caracterización previa**: la suite de H-API-14 completa (listado, creación, resumen, subida, `backend-health` y 401) en verde antes de mover código, y repetida sin cambios de expectativas después de la extracción.

### H-API-07 — Calidad: `dict`, excepciones amplias, anidamiento, duplicación

- **Hallazgo**: `HALLAZGOS.md` H-API-07 (Refactor, media).
- **Problema**: `dict[str, Any]` crudo, `except Exception` (api/app/main.py:25, 120), `if` anidados (101-104), duplicación (69 y 92) y strings mágicos.
- **Cambio propuesto** (modelos Pydantic y Clean Code):
  - `schemas.py`: `TaskCreateRequest`, `TaskResponse` (con alias `createdAt`, para conservar el JSON), `TaskSummaryResponse` (`owner`, `total`, `byStatus`, `highPriorityOpen`), `RequirementUploadResponse`, `BackendHealthResponse`, `Identity`. Cada ruta declara `response_model` y tipos concretos.
  - `summary`: una función `count_by_status` (`collections.Counter`) y otra `count_high_priority_open` con condición combinada (`priority == HIGH and status not in CLOSED_STATUSES`); sin anidamiento.
  - Capturar excepciones concretas (`sqlite3.Error`, `urllib3.exceptions.HTTPError`, `ValueError`) en lugar de `Exception`.
  - Constantes con nombre en `constants.py`: estados, prioridades, `CLOSED_STATUSES`, valores por defecto y la URL por defecto de health.
  - Una sola función `resolve_owner` (ver H-API-03) en lugar de repetir `owner or identity["username"]`.
- **Contrato**: formato JSON idéntico, incluida la clave `createdAt`.
- **Archivos a tocar**: api/app/schemas.py, api/app/services.py, api/app/constants.py, api/app/routes.py, api/tests/test_summary.py (nuevo).
- **Prueba de caracterización previa**: dataset ficticio con combinaciones de `status` (`TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`) y `priority` (`HIGH`, `MEDIUM`, `LOW`) que fija `total`, `byStatus` y `highPriorityOpen` actuales; debe pasar igual antes y después. Además, una prueba que fija las claves exactas de la respuesta de tareas.

### H-API-08 — Errores con detalle interno

- **Hallazgo**: `HALLAZGOS.md` H-API-08 (Vulnerabilidad, media).
- **Problema**: el `401` concatena `str(error)` (api/app/main.py:26) y `backend-health` devuelve el texto de la excepción y el cuerpo del servicio auth (119-121).
- **Cambio propuesto**: `HTTPException` con mensajes genéricos constantes (por ejemplo `"Invalid or expired token"`); el detalle se envía solo al log del servidor con `logging` (sin tokens ni datos personales en el log). `backend-health` devuelve `status` y un `body` genérico ante error, y no reenvía el cuerpo crudo de auth (ver H-API-11 para su forma exacta).
- **[Decisión]**: el texto exacto del mensaje del `401`; `web` podría depender del texto actual (no verificable desde este plan, se deja pendiente).
- **Archivos a tocar**: api/app/security.py, api/app/services.py, api/app/constants.py, api/tests/test_errors.py (nuevo).
- **Prueba de caracterización previa**: registrar el `detail` actual del `401` para token no Base64 (contiene la causa interna); tras el cambio afirmar que el `detail` es genérico y no contiene nombres de excepción ni mensajes de Python. Para `backend-health`, apuntar `AUTH_HEALTH_URL` a un puerto local sin servicio y comprobar que la respuesta no contiene el texto de la excepción.

### H-API-09 — CORS permisivo

- **Hallazgo**: `HALLAZGOS.md` H-API-09 (Vulnerabilidad, media).
- **Problema**: `allow_origins=["*"]` con `allow_credentials=True` (api/app/main.py:48-54).
- **Cambio propuesto**: orígenes leídos de una variable de entorno (por ejemplo `WORKSHOP_CORS_ORIGINS`, lista separada por comas) con valor por defecto para el laboratorio `http://localhost:4200` (puerto de `web` según `README.md`). Métodos y cabeceras limitados a los usados (`GET`, `POST`, `OPTIONS`; `Authorization`, `Content-Type`). Esta convención no figura en `docs/GOOD_PRACTICES.md` (sección api): es una propuesta sujeta a aprobación. Validar el valor de `compose.yaml` para no romper el arranque con Compose (el archivo está fuera del alcance de escritura de api; si requiere cambio, se coordina).
- **Archivos a tocar**: api/app/config.py, api/app/main.py, api/tests/test_cors.py (nuevo).
- **Prueba de caracterización previa**: petición `OPTIONS` con `Origin` ficticio hoy es aceptada (queda registrado); tras el cambio, un origen no permitido no recibe `access-control-allow-origin` y el origen configurado sí.

### H-API-10 — Sin validación de dominio en el body de tareas

- **Hallazgo**: `HALLAZGOS.md` H-API-10 (Bug, media).
- **Problema**: cualquier cadena es válida para `status`, `priority` y `title`; `str(...)` convierte tipos arbitrarios (api/app/main.py:79-83).
- **Cambio propuesto**: `TaskCreateRequest` (Pydantic) con `title: str` (longitud mínima y máxima), `description: str`, `status: TaskStatus = TODO`, `priority: TaskPriority = MEDIUM` (enums con los valores observados: `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`; `HIGH`, `MEDIUM`, `LOW`) y límites de longitud como constantes. El campo `owner` del body se acepta pero se ignora (ver H-API-03) para no romper clientes que lo envíen. FastAPI responde `422` ante datos inválidos.
- **[Decisión]**: hoy un body sin `title` o con valores libres se acepta; rechazarlo cambia el comportamiento observado. Hay que confirmar que `web` solo envía los valores listados, y fijar los límites. El conjunto de estados `ARCHIVED` y `DONE` se infiere de `summary`; no hay lista oficial.
- **Archivos a tocar**: api/app/schemas.py, api/app/constants.py, api/tests/test_task_validation.py (nuevo).
- **Prueba de caracterización previa**: crear tarea con los valores por defecto (solo `title`) y comprobar `status=TODO`, `priority=MEDIUM`, `owner` del token; registrar que hoy un `status` libre se acepta. Tras el cambio: `422` para valores fuera del enum o `title` vacío.

### H-API-11 — `backend-health` abierto y con URL del entorno

- **Hallazgo**: `HALLAZGOS.md` H-API-11 (Sugerencia, baja).
- **Problema**: cualquier identidad válida consulta el estado y el cuerpo de `auth`; se crea un `PoolManager` por llamada (api/app/main.py:114-121).
- **Cambio propuesto**: `BackendHealthService` con un `PoolManager` reutilizado (creado en `create_app`), timeout y URL por defecto como constantes, validación del esquema (`http`/`https`) de `AUTH_HEALTH_URL` al arrancar, y respuesta limitada a `requestedBy`, `status` y un `body` acotado. Se mantiene el endpoint y el formato `{requestedBy, status, body}`.
- **[Decisión]**: si la ruta debe exigir un rol. No está definido; se deja sin restricción de rol hasta que el contrato lo indique.
- **Archivos a tocar**: api/app/services.py, api/app/config.py, api/app/constants.py, api/tests/test_backend_health.py (nuevo).
- **Prueba de caracterización previa**: con el cliente HTTP simulado (sin llamada de red real), `200` de auth devuelve `status` 200 y el cuerpo; falla de conexión devuelve `status` 0; token inválido `401`.

### H-API-12 — Conexión SQLite compartida

- **Hallazgo**: `HALLAZGOS.md` H-API-12 (Bug, baja, hipótesis sin reproducir).
- **Problema**: una única conexión con `check_same_thread=False` y sin sincronización (api/app/main.py:35); cierre con `on_event("shutdown")` (123-125).
- **Cambio propuesto**: el repositorio abre una conexión por operación (contexto `with`) o usa un `Lock` explícito; se elige la opción más simple tras reproducir el problema con una prueba concurrente. El cierre pasa a un manejador `lifespan` de FastAPI en lugar de `on_event`. Sin dependencias nuevas.
- **Archivos a tocar**: api/app/repository.py, api/app/main.py, api/tests/test_concurrency.py (nuevo).
- **Prueba de caracterización previa**: varias peticiones concurrentes de `POST /api/tasks` y `GET /api/tasks` con DB temporal (hilos con `TestClient`); registrar el resultado actual. Si no se reproduce el fallo, se documenta que el cambio es preventivo.

### H-API-13 — Efectos secundarios al importar `app.main`

- **Hallazgo**: `HALLAZGOS.md` H-API-13 (Refactor, baja).
- **Problema**: `app = create_app()` (api/app/main.py:130) crea directorios y la base al importar.
- **Cambio propuesto**: conservar `app` para `uvicorn app.main:app` (Dockerfile y `README.md`), pero crearlo de forma perezosa (por ejemplo una función factoría `get_app()` o `uvicorn --factory`) solo si se aprueba cambiar el comando; si no, mantener `app` y mover la creación de directorios y DB a `lifespan`, de modo que importar el módulo no toque el disco.
- **[Decisión]**: cambiar el comando de arranque afectaría `api/Dockerfile`, `tools/lab.py` y Compose; se recomienda la segunda opción (mantener `app`, mover la inicialización al arranque) para no alterar el contrato de despliegue.
- **Archivos a tocar**: api/app/main.py, api/tests/test_startup.py (nuevo).
- **Prueba de caracterización previa**: importar `app.main` en un directorio temporal y comprobar qué crea hoy (carpetas `data` y `uploads`); tras el cambio, afirmar que importar no crea nada y que el arranque (`TestClient` como contexto) sí inicializa la base.

### H-API-14 — Cobertura limitada al camino feliz

- **Hallazgo**: `HALLAZGOS.md` H-API-14 (Sugerencia, media).
- **Problema**: solo hay 4 pruebas (api/tests/test_api.py); no cubren `owner` ajeno, comillas, token expirado o malformado, `backend-health` ni nombres de archivo peligrosos.
- **Cambio propuesto**: ampliar la suite **antes** de cualquier cambio de código, con DB y directorio temporales (`tmp_path`), datos ficticios y sin red real. Un `conftest.py` con fixtures `client`, `auth_headers` y fábrica de tokens evita duplicar el helper de `test_api.py`. Las pruebas que fijan comportamiento inseguro actual se nombran y marcan para invertirse en el hallazgo que lo corrige (H-API-01, 03, 04, 08), sin dejarlas como si fueran requisitos. Comando: `python tools/lab.py test api` desde la raíz, o `pytest` con cwd `api/`.
- **Archivos a tocar**: api/tests/conftest.py (nuevo), api/tests/test_characterization.py (nuevo), api/tests/test_api.py (reutiliza fixtures).
- **Prueba de caracterización previa**: no aplica (es la propia suite). Criterio de salida: toda la suite verde sobre el código actual y registro de numerador, denominador y método de cobertura en `docs/TESTING.md`; no se afirma cobertura sin ejecutarla.

---

### Aprobación humana registrada

- 2026-11-02 16:36 (-05:00): el usuario respondió en el chat "apruebo todos los cambios mencionados" sobre este plan. Se interpreta como aprobación de los cambios propuestos y de la opción recomendada en cada **[Decisión]**:

| Hallazgo | Decisión aprobada (opción recomendada) |
|---|---|
| H-API-03 | `owner` distinto al de la identidad → `403`; el `owner` del body se ignora. Sin regla de roles. |
| H-API-04 | Extensiones `.txt`, `.md`, `.pdf`; máximo 1 MiB; `storedAt` se conserva con solo el nombre almacenado. Política ante nombre repetido: pendiente de definir al implementar. |
| H-API-08 | Mensajes genéricos en `401` y en `backend-health`; detalle solo al log. |
| H-API-10 | Enums de `status`/`priority`, `title` no vacío y `422` ante datos inválidos; límites de longitud como constantes. |
| H-API-11 | Sin restricción de rol en `backend-health`. |
| H-API-13 | Mantener `app` y mover la inicialización a `lifespan`. |

- Esta aprobación no cubre H-API-02: el contrato del JWT sigue pendiente de acuerdo con `auth`. Tampoco sustituye la revisión humana del código ni las pruebas reales.

### Riesgos y pendientes abiertos

- Formato del token acordado con `auth` (H-API-02): bloquea la entrega end-to-end con `web`.
- Decisiones **[Decisión]** de H-API-03, 04, 08, 10, 11 y 13: aprobadas en el chat (ver "Aprobación humana registrada"); falta la política de nombre repetido en H-API-04.
- No se pudo comprobar qué espera `web` de `storedAt`, del texto del `401` ni de los valores de `status`/`priority` (fuera del alcance de lectura).
- Cobertura del código modificado: 100% de rama sobre todo `app` (293 sentencias, 20 ramas, 0 fallos) con `python tools/lab.py test api`; es cobertura total de la app, no del diff aislado. Se registrará en `docs/TESTING.md` en su paso.
- Rama: `day1/prompting` (creada desde `main`).

### Registro de ejecuciones (componente api)

Entorno: `api/.venv`, Python 3.13.15, cwd `api/`. Comando base: `.\.venv\Scripts\python.exe -m pytest` (equivale al de `tools/lab.py`, con `--cov=app --cov-fail-under=85`).

| # | IDs | Momento | Comando / archivo | Resultado |
|---|---|---|---|---|
| 1 | todos (línea base) | antes de cambios | `python -m pytest --cov=app --cov-fail-under=85` (4 pruebas originales) | 4 passed; cobertura 91.07% |
| 2 | H-API-14 (caracterización) | código legado | `tests/test_characterization.py` | 30 passed |
| 3 | H-API-01, 03, 04, 07, 08, 09, 10, 11, 12, 13 (corrección) | código legado | `tests/test_corrections_api.py` | 33 failed, 3 passed (los 3 son controles positivos: propio `owner`, archivo en el límite, CORS del origen permitido). H-API-12 reprodujo respuestas 500 con 8 hilos concurrentes |
| 4 | H-API-05 | antes | consulta OSV `urllib3 2.5.0` / `python-multipart 0.0.21` | 6 y 7 CVEs respectivamente |
| 5 | H-API-05 | después | `pip install -r requirements.txt -r requirements-dev.txt`, `pip check`, consulta OSV `urllib3 2.8.0` / `python-multipart 0.0.33` | instalado sin conflictos; `No broken requirements found`; OSV sin advisories (respuesta vacía); `test_characterization.py` + `test_api.py`: 34 passed |
| 6 | H-API-01, 02 (parcial: solo 401 genérico), 03, 04, 06, 07, 08, 09, 10, 11, 12, 13 | tras el refactor | `python -m pytest` (suite completa) | 70 passed |
| 7 | los anteriores + unitarias | final | `tests/test_units.py` + suite | 106 passed |
| 8 | H-API-14 y todos | final | `python tools/lab.py test api` (desde la raíz) | 106 passed, 1 warning (deprecación de Starlette `TestClient`, ajena al código); cobertura 100%; `api/htmlcov/index.html` |
| 9 | H-API-06, 13 | final | arranque real `uvicorn app.main:app` en puerto 8765 con base temporal; `GET /api/summary` con token legado válido; `GET /api/tasks?owner=trainer` | 200 con `{"owner":"student","total":2,...}`; 403 |
| 10 | H-API-14 (estabilidad) | revisión local | `python -m pytest` ×5 | 106 passed en las 5 ejecuciones |
| 11 | H-API-05 (revisión) | revisión local | consulta OSV de las dependencias instaladas en `api/.venv` | `starlette 0.50.0`: 5 advisories distintos (corregidos en 1.0.1+); `pytest 9.0.2`: CVE-2025-71176 (corregido en 9.0.3); resto sin advisories. H-API-05 vuelve a Pendiente (parcial) |
| 12 | H-API-02, 03, 04, 08, 10, 11 (documentación) | documentación de contrato | script local con `TestClient`, base y directorio temporales, datos ficticios y `urllib3` simulado para `backend-health`; sin cambios de código | Respuestas reales capturadas para cada endpoint y error; usadas como ejemplos en `docs/ENDPOINTS.md` |
| 13 | H-API-14 y pruebas por endpoint de `docs/ENDPOINTS.md` | pruebas de contrato | `python -m pytest --cov=app --cov-fail-under=85` (cwd `api/`) y `python tools/lab.py test api` (raíz); detalle en `docs/TESTING.md` | 165 passed, exit 0 en ambos; cobertura 313/313 (sentencias + ramas) = 100%, tanto del código modificado como global; 3 repeticiones sin fallos |

Revisión local 2026-11-02: H-API-04 y H-API-05 vuelven a "Pendiente (parcial)" en `HALLAZGOS.md`; H-API-03 queda "Resuelto" condicionado a H-API-02. Sin aprobación humana de cierre registrada.

No ejecutado: Compose y pruebas de integración con `web`/`auth`; ninguna prueba contra servicios remotos.

### Desviaciones del plan

- **H-API-02 no implementado**: el contrato del JWT no está acordado con `auth`; sigue `Pendiente`. Solo se aplicó su parte compartida con H-API-08 (401 genérico). El secreto legado sigue en `api/app/security.py` con un comentario que lo señala.
- **H-API-04**: no se añadió `resolve_target` (comprobación de que la ruta resuelta queda en el directorio de subidas); el nombre normalizado solo contiene `[A-Za-z0-9._-]`, sin separadores, y los nombres `.`/`..` se rechazan, por lo que esa rama sería inalcanzable. La política de nombre repetido no se definió: se conserva la sobrescritura observada. El límite de 1 MiB se aplica al leer el contenido; Starlette ya recibió el cuerpo multipart en un archivo temporal, por lo que un límite de cuerpo en el servidor/proxy queda como mejora aparte.
- **H-API-06/07**: se añadieron `api/tests/test_units.py` y `Identity` como modelo Pydantic; la estructura de módulos coincide con el plan.
- **H-API-09**: se añadió `http://127.0.0.1:4200` a los orígenes por defecto además de `http://localhost:4200`.
- **H-API-12**: se eligió una conexión por operación (sin `Lock`).
- **H-API-13**: el apartado de `README`/Compose no cambia; `uvicorn app.main:app` sigue funcionando.
- **H-API-14**: las pruebas de corrección de H-API-05 (OSV, `pip check`) se ejecutaron como comandos, no como pruebas pytest.
- La rama `day1/prompting` no existía y se creó para trabajar (README); los cambios no están commiteados.

## web

### H-WEB-01 — Resolución de advisories en dependencias directas

- **Aprobación:** H-WEB-01 y su spec/impacto fueron aprobados antes de implementar. El alcance es solo axios y lodash; no se creó un issue externo.
- **Contexto:** axios se usa para `POST /auth/login` y `GET /api/tasks`; lodash `merge` combina preferencias locales con defaults. Las versiones iniciales eran `axios 0.31.0` y `lodash 4.17.21`.
- **Decisión — axios:** conservar el cliente HTTP y actualizar a `0.34.0`; OSV reporta dos advisories en `0.33.0` y ninguno en `0.34.0`. Se conservan las llamadas existentes sin migrar a Angular `HttpClient`.
- **Decisión — lodash:** conservar `merge` y actualizar a `4.18.1`. La retirada no se eligió porque no se caracterizó una alternativa equivalente a la mezcla actual; la versión seleccionada no presenta advisories OSV.
- **Consecuencias:** `web/package.json` y `web/package-lock.json` se actualizan juntos. Se agregan pruebas de caracterización de login y dashboard; no cambia código de producción ni el formato de los endpoints.
- **Riesgo residual:** `npm audit` aún reporta 41 hallazgos (incluidos 7 de dependencias runtime); se dejan visibles y fuera del alcance. El build mantiene advertencias CommonJS para axios y lodash.
- **Evidencia:** ver [docs/TESTING.md](./docs/TESTING.md), sección `web`; cierre de H-WEB-01 en [HALLAZGOS.md](./HALLAZGOS.md). No se ejecutó integración real con `auth`/`api`.
