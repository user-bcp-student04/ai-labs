# Hallazgos de ReqFlow

Seguimiento único de hallazgos. Las referencias son `archivo:línea` desde la raíz del repositorio. Cada componente mantiene sus propias filas e IDs; no renumerar IDs existentes. `2-refactor.md` actualiza el estado hallazgo por hallazgo.

Estados permitidos: `Pendiente`, `No encontrado` y los que añada el refactor con evidencia real.

## api

### Alcance y método de la fase Discovery

- Componente: `api` (FastAPI + SQLite). Solo se leyó código de `api/`; no se modificó ningún archivo de código.
- Fuentes leídas: `README.md`, `RETO.md`, `docs/GOOD_PRACTICES.md`, `api/app/main.py`, `api/tests/test_api.py`, `api/requirements.txt`, `api/requirements-dev.txt`, `api/pyproject.toml`, `api/Dockerfile`.
- `docs/ENDPOINTS.md` **no existe** en este momento: el contrato de abajo es *observado en el código* (no acordado). No se crea en este paso.
- No se ejecutaron pruebas ni ataques. Los hallazgos de código son lectura estática. Los advisories de dependencias se consultaron en OSV (`https://api.osv.dev/v1/query`, paquete + versión).
- Las 7 filas de `RETO.md` (api) existen en el código: ninguna queda como `No encontrado`. Las filas H-API-08 a H-API-14 son adicionales, detectadas durante la lectura (no figuran en `RETO.md`).

### Matriz de seguimiento

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-API-01 | api | SQL concatenado con entrada del cliente (filtro `owner`, campos de tarea) | Vulnerabilidad | `owner` (query), y `title`, `description`, `status`, `priority`, `owner` (body) se concatenan en el SQL sin parametrizar. Una comilla en el dato altera la consulta: puede filtrar o leer filas de otros owners, o corromper/forzar inserts. `sqlite3.execute` rechaza varias sentencias, pero SELECT/INSERT siguen siendo manipulables. Solo el `lastrowid` del SELECT final (entero generado por SQLite) es seguro en la práctica. | api/app/main.py:70-71 (GET /api/tasks); api/app/main.py:79-85 (POST /api/tasks); api/app/main.py:87 (SELECT por `lastrowid`, no controlado por el cliente); api/app/main.py:93 (GET /api/summary) | alta | Resuelto. Todo el SQL vive en `TaskRepository` con placeholders `?` (api/app/repository.py:9-21, 54-65); pruebas: test_units.py (repositorio), test_corrections_api.py (H-API-01). |
| H-API-02 | api | Token Base64 con secreto embebido y sin firma real | Vulnerabilidad | El token es `base64(usuario\|rol\|exp\|secreto)`: cualquiera que conozca el secreto (está en el repositorio y en las pruebas) forja identidad y rol. No hay firma criptográfica, emisor ni audiencia; la comparación del secreto no es en tiempo constante; `Bearer ` se quita con `replace` (acepta basura). Interopera con auth: cambiar el formato exige coordinar con ese componente. | api/app/main.py:14 (secreto); api/app/main.py:19-24 (decodificación y validación); api/tests/test_api.py (fabrica tokens con el mismo secreto) | alta | Pendiente. Bloqueado: el contrato del JWT debe acordarse con `auth`. Solo se aplicó la parte de H-API-08 (401 genérico) en api/app/security.py. |
| H-API-03 | api | El cliente puede consultar y asignar otro `owner` (sin autorización por identidad/rol) | Vulnerabilidad | `owner` llega por query y manda sobre `identity["username"]`: cualquier usuario autenticado lee tareas y resumen de otro. En POST el `owner` del body permite crear tareas a nombre de otro. El `role` del token se devuelve pero nunca se usa. | api/app/main.py:69 (list_tasks); api/app/main.py:83 (create_task); api/app/main.py:92-94 (summary); api/app/main.py:24 (role sin uso posterior) | alta | Resuelto en el código (revisión local 2026-11-02: `resolve_owner`, api/app/services.py:40-43, usa siempre la identidad; un `owner` ajeno da 403 y el `owner` del body se ignora). Condicionado a H-API-02: mientras el token sea forjable (api/app/security.py:13, 19), la identidad no es confiable. Sin regla de roles (no definida). |
| H-API-04 | api | Subida de archivos con `upload.filename` directo, sin límite de extensión ni tamaño | Vulnerabilidad | `Path(uploads) / file.filename` usa el nombre del cliente: riesgo de path traversal (hipótesis: no ejecutado), sobrescritura de archivos existentes, extensiones arbitrarias y consumo de memoria/disco al leer todo el contenido con `file.read()`. La respuesta devuelve además la ruta absoluta/relativa del servidor. | api/app/main.py:108-112 (nombre en 109, lectura completa en 110, escritura en 111, `storedAt` en 112) | alta | Pendiente (parcial, revisión local 2026-11-02). Corregido: nombre normalizado, extensiones `.txt/.md/.pdf`, `storedAt` sin ruta (api/app/services.py:72-108). No corregido: (1) el límite de 1 MiB se aplica en api/app/services.py:85-93 después de que Starlette ya recibió y volcó el archivo completo a disco temporal (api/.venv/.../starlette/formparsers.py:126, 209; `max_part_size` solo limita campos no archivo, línea 163), así que sigue habiendo consumo de disco/tiempo sin tope; (2) los archivos comparten un único directorio y se sobrescriben por nombre (api/app/services.py:104), por lo que un usuario puede reemplazar el archivo de otro. |
| H-API-05 | api | Dependencias con CVEs conocidos: `urllib3 2.5.0` y `python-multipart 0.0.21` | Vulnerabilidad | OSV reporta para urllib3 2.5.0: CVE-2025-66418, CVE-2025-66471, CVE-2026-21441, CVE-2026-44431, CVE-2026-97687, CVE-2026-97689 (DoS por descompresión/streaming, cabeceras sensibles en redirecciones, proxy TLS). Para python-multipart 0.0.21: CVE-2026-24486 (escritura arbitraria de archivos, config no por defecto), CVE-2026-40347, -42561, -53537, -53538, -53539, -53540 (DoS y parameter smuggling en parsing multipart/querystring). El endpoint de subida y `backend-health` usan estas librerías. Versión corregida exacta pendiente de confirmar al actualizar y probar compatibilidad con FastAPI. | api/requirements.txt:4 (urllib3==2.5.0); api/requirements.txt:5 (python-multipart==0.0.21); api/app/main.py:10 y api/app/main.py:118 (uso de urllib3) | media | Pendiente (parcial, revisión local 2026-11-02). Corregido: `urllib3==2.8.0` y `python-multipart==0.0.33` (api/requirements.txt:4-5), sin advisories en OSV. No corregido: `fastapi==0.128.2` (api/requirements.txt:1) exige `starlette<0.51` y arrastra `starlette 0.50.0`, con 5 advisories distintos en OSV (CVE-2026-48710, -48817, -48818, -54282, -54283; corregidos en starlette 1.0.1 o superior, lo que requiere una versión mayor de FastAPI). En desarrollo, `pytest==9.0.2` (api/requirements-dev.txt:1) tiene CVE-2025-71176 (corregido en 9.0.3). |
| H-API-06 | api | Arquitectura monolítica: rutas, DB, reglas y serialización en un solo archivo | Refactor | `create_app` crea la conexión, el esquema, el seed, el CORS, las rutas (cierres) y el SQL. No se puede probar ni sustituir cada capa por separado; el refactor de seguridad (H-API-01/03) es más riesgoso sin esta separación. | api/app/main.py:29-127 (`create_app`); api/app/main.py:35-43 (DB y seed); api/app/main.py:56-65 (serialización); api/app/main.py:67-112 (rutas con SQL); api/app/main.py:130 (instancia global) | media | Resuelto. Capas ruta (routes.py) → servicio (services.py) → repositorio (repository.py), con config, constants, schemas y security; `main.py` solo cablea (api/app/main.py:15-40). |
| H-API-07 | api | Calidad: `dict[str, Any]` crudo, `except Exception` amplios, `if` anidados y duplicación | Refactor | Sin modelos Pydantic no hay validación de entrada/salida (p. ej. `str(payload.get(...))` convierte cualquier tipo). `except Exception` oculta fallos. `summary()` anida 3 `if` y cuenta a mano. El cálculo `owner or identity["username"]` y los bucles de conteo/serialización se repiten. Strings mágicos (`"HIGH"`, `"DONE"`, `"ARCHIVED"`, `"TODO"`, `"MEDIUM"`, URL por defecto). | api/app/main.py:17 y api/app/main.py:56-65 (`dict` crudo); api/app/main.py:25 y api/app/main.py:120 (`except Exception`); api/app/main.py:101-104 (anidamiento); api/app/main.py:69 y api/app/main.py:92 (duplicación); api/app/main.py:79-83 (strings por defecto); api/app/main.py:96-100 (conteo manual) | media | Resuelto. Modelos Pydantic (api/app/schemas.py), `Counter` y `is_high_priority_open` sin anidamiento, excepciones concretas y constantes con nombre (api/app/constants.py). |
| H-API-08 | api | Errores exponen detalle interno (`str(error)`) | Vulnerabilidad | El 401 concatena la excepción original (p. ej. error de Base64 o `int()`), ayudando a un atacante a afinar tokens falsos; `backend-health` devuelve el texto de la excepción de red y el cuerpo crudo de la respuesta del servicio auth. | api/app/main.py:26; api/app/main.py:119-121 | media | Resuelto. 401 con mensaje genérico y `backend-health` con `body` genérico ante fallo; el detalle va solo al log (api/app/security.py:33-39, api/app/services.py:115-123). |
| H-API-09 | api | CORS permisivo: `allow_origins=["*"]` con `allow_credentials=True` | Vulnerabilidad | Cualquier origen puede invocar la API desde un navegador; combinar comodín y credenciales es una mala configuración (los navegadores lo restringen, pero indica política no definida). Debe externalizarse por ambiente. | api/app/main.py:48-54 | media | Resuelto. Orígenes desde `WORKSHOP_CORS_ORIGINS` (por defecto `http://localhost:4200` y `http://127.0.0.1:4200`), métodos y cabeceras acotados (api/app/config.py, api/app/main.py:29-34). |
| H-API-10 | api | Sin validación de dominio en el body de tareas (`status`, `priority`, longitudes) | Bug | Se acepta cualquier cadena como `status`/`priority`/`title` (incluso vacíos); `summary` solo reconoce `HIGH`, `DONE`, `ARCHIVED`, por lo que valores libres rompen los contadores. Contrato aceptado hoy: `title`, `description`, `status` (por defecto `TODO`), `priority` (por defecto `MEDIUM`). Cualquier restricción nueva debe acordarse antes de cambiar el contrato. | api/app/main.py:79-83; api/app/main.py:101-103 | media | Resuelto. `TaskCreateRequest` con enums de estado/prioridad, `title` 1-200 y `description` hasta 2000; 422 ante datos inválidos (api/app/schemas.py:15-19). |
| H-API-11 | api | `GET /api/backend-health` abierto a cualquier usuario autenticado y con URL tomada del entorno | Sugerencia | Devuelve estado y cuerpo del servicio auth a cualquier identidad válida, sin rol; la URL viene de `AUTH_HEALTH_URL` (configurable, no del cliente: riesgo SSRF bajo, pero conviene validar el esquema/host). Se crea un `PoolManager` nuevo en cada llamada. | api/app/main.py:114-121 | baja | Resuelto. `PoolManager` reutilizado, esquema de `AUTH_HEALTH_URL` validado (http/https), `body` limitado a 1000 caracteres; sin restricción de rol (no definida). api/app/services.py:110-125, api/app/config.py. |
| H-API-12 | api | Una única conexión SQLite compartida con `check_same_thread=False` y sin sincronización | Bug | FastAPI ejecuta rutas síncronas en un pool de hilos; compartir la misma conexión sin lock puede dar errores intermitentes en concurrencia (hipótesis, no reproducida). El cierre se hace con `on_event("shutdown")`, API obsoleta en FastAPI. | api/app/main.py:35; api/app/main.py:123-125 | baja | Resuelto. Reproducido antes del cambio (500 con 8 hilos concurrentes); ahora cada operación abre su conexión (api/app/repository.py:66-73) y se eliminó `on_event`. |
| H-API-13 | api | Efectos secundarios al importar el módulo (`app = create_app()`) | Refactor | Importar `app.main` crea directorios y la base `./data/workshop.db` aunque solo se quiera usar `create_app` en pruebas. | api/app/main.py:130; api/app/main.py:30-33 | baja | Resuelto. `app` se conserva, pero la creación de carpetas y base se hizo en `lifespan` (api/app/main.py:19-23); importar el módulo ya no toca el disco. |
| H-API-14 | api | Cobertura de pruebas limitada al camino feliz | Sugerencia | Las 4 pruebas actuales cubren listado, creación + resumen, subida válida y un token inválido. No hay pruebas de caracterización para `owner` ajeno, comillas en entradas, token expirado/malformado, `backend-health` ni nombres de archivo peligrosos. Necesarias antes del refactor (meta 85% del código modificado). | api/tests/test_api.py (4 funciones `test_*`); api/pyproject.toml:1-11 (config de pytest/coverage) | media | Resuelto. 106 pruebas (api/tests/conftest.py, test_characterization.py, test_corrections_api.py, test_units.py, test_api.py); cobertura de rama 100% de `app` con `python tools/lab.py test api`. |

> Orden: severidad alta → media → baja. Las filas de la misma severidad se ordenan por prioridad de remediación (los hallazgos de `RETO.md` primero).
>
> Las líneas de la columna de evidencia corresponden al código original (commit `16b54a3`, `api/app/main.py` monolítico); la nota de cada fila "Resuelto" cita la ubicación actual. Ejecuciones y resultados: ver "Registro de ejecuciones" en `PLAN.md`.

### Mapeo con `RETO.md` (api)

| Área en RETO.md | Hallazgo | Resultado |
|---|---|---|
| SCA | H-API-05 | Encontrado |
| Auth | H-API-02 | Encontrado |
| Autorización | H-API-03 | Encontrado |
| SQL | H-API-01 | Encontrado |
| Files | H-API-04 | Encontrado |
| Arquitectura | H-API-06 | Encontrado |
| Calidad | H-API-07 | Encontrado |

### Contrato observado (derivado del código; no acordado)

`docs/ENDPOINTS.md` no existe; esto debe revisarse con el equipo antes de tomarlo como contrato acordado.

| Endpoint | Entrada | Autenticación | Respuesta observada | Riesgos pendientes |
|---|---|---|---|---|
| `GET /api/tasks` | query `owner` (opcional; por defecto el usuario del token) | Cabecera `Authorization: Bearer <token>`; 401 si es inválido (main.py:17-26) | 200, lista de `{id,title,description,status,owner,priority,createdAt}` ordenada por `id` (main.py:56-75) | H-API-01, H-API-03, H-API-07 |
| `POST /api/tasks` | JSON con `title`, `description`, `status`=TODO, `priority`=MEDIUM, `owner`=usuario del token | Igual | 201, la tarea creada con el mismo formato (main.py:77-88) | H-API-01, H-API-03, H-API-10 |
| `GET /api/summary` | query `owner` (opcional) | Igual | 200, `{owner,total,byStatus,highPriorityOpen}`; `highPriorityOpen` cuenta prioridad `HIGH` con estado distinto de `DONE`/`ARCHIVED` (main.py:90-105) | H-API-01, H-API-03, H-API-07 |
| `POST /api/requirements` | multipart, campo `file` | Igual | 201, `{owner,fileName,storedAt,size}` (main.py:107-112) | H-API-04, H-API-05 |
| `GET /api/backend-health` | — | Igual | 200, `{requestedBy,status,body}`; si falla, `status:0` y `body` con el error (main.py:114-121) | H-API-08, H-API-11 |

### Flujo mapeado

- **Token**: `Authorization` → quitar `Bearer ` → Base64 → `usuario|rol|exp|secreto` → válido si hay 4 partes, el secreto coincide y `exp` ≥ ahora (main.py:19-24). Devuelve `{username, role}`. Cualquier fallo → 401 con `"Invalid token: " + str(error)` (main.py:26). Sin cabecera → cadena vacía → 401.
- **SQLite**: conexión única creada al armar la app (main.py:35-36); esquema y seed de 3 tareas si la tabla está vacía (main.py:37-43). Lectura y escritura concatenadas (main.py:70, 84, 93). Ninguna consulta usa parámetros `?`.
- **Archivos**: `selected_uploads` (`WORKSHOP_UPLOAD_DIR` o `./uploads`) + `file.filename` sin normalizar (main.py:31, 109); contenido completo en memoria y escritura directa (main.py:110-111).

### Pendientes y límites de esta evidencia

- Las pruebas del refactor se ejecutaron localmente (ver `PLAN.md`); las hipótesis de path traversal y de concurrencia quedaron cubiertas por pruebas con datos ficticios (la concurrencia se reprodujo antes del cambio).
- H-API-02 sigue `Pendiente`: falta acordar con `auth` el contrato del JWT. No se confirmó con `web` el uso de `storedAt`, del texto del 401 ni de los valores de `status`/`priority`.
- Compatibilidad real con `web`/`auth` (Compose): no probada.
- `docs/ENDPOINTS.md` no existe; el contrato acordado queda pendiente de definir (se conserva el comportamiento observado, con los cambios aprobados en `PLAN.md`).
- Se creó la rama local `day1/prompting` desde `main` (no existía) para trabajar el Día 1. Los cambios están sin commitear (no se pidió commit).

## web

### Alcance y método de la fase Discovery

- Componente: `web` (Angular 21, standalone). Solo se leyó código de `web/` y los documentos compartidos `RETO.md` (sección web) y `docs/ENDPOINTS.md` (solo para contrastar valores de `status`/`priority`; esa sección no documenta `web`). No se leyó `auth` ni `api`; no se modificó código.
- Comandos ejecutados (desde `web/`, solo lectura): `npx vitest run --coverage`, `npm audit --audit-level=moderate`, consulta OSV (`https://api.osv.dev/v1/query`, paquete + versión) y un `node -e` con datos ficticios para el orden por prioridad.
- H-WEB-01 fue aprobado para implementación; H-WEB-02 a H-WEB-05 permanecen `CANDIDATO` y requieren revisión humana. No se crearon issues. Referencias `archivo:línea` desde la raíz.

### H-WEB-01 — Dependencias con advisories: `axios 0.31.0` y `lodash 4.17.21`
- Estado: Resuelto en el alcance aprobado; revisión humana de cierre pendiente.
- Evidencia: web/package.json:14-15 (`"axios": "0.31.0"`, `"lodash": "4.17.21"`). OSV: axios 0.31.0 con 23 advisories (p. ej. CVE-2026-44495, CVE-2026-42041, CVE-2026-42035, CVE-2026-42033; correcciones en 0.31.1, 0.32.0, 0.33.0 y 0.34.0 según el advisory) y lodash 4.17.21 con 2 (CVE-2025-13465 corregido en 4.17.23; CVE-2026-4800 corregido en 4.18.0). `npm audit --audit-level=moderate`: 43 vulnerabilidades en total (27 moderate, 10 high, 6 critical), que incluyen dependencias transitivas de desarrollo (p. ej. `zod`), no todas distinguidas por directa/runtime. Uso real: axios en web/src/app/login/login.component.ts:41 y web/src/app/dashboard/dashboard.component.ts:43; lodash solo `merge` en web/src/app/login/login.component.ts:6 y :25.
- Resultado: versiones fijadas en `axios 0.34.0` y `lodash 4.18.1` en web/package.json y web/package-lock.json. Consulta OSV de ambas versiones: 0 advisories. `npm ls axios lodash --depth=0` confirma las versiones instaladas. `npm audit` pasó de 43 a 41 vulnerabilidades (27 moderate, 8 high, 6 critical); `npm audit --omit=dev` conserva 7 hallazgos (5 moderate, 2 high) en Angular y `follow-redirects`, fuera del alcance aprobado. No se silenció el scanner.
- Impacto: varios advisories de axios son de gadgets de prototype pollution y cabeceras que podrían aplicar al navegador; otros son del adaptador Node (proxy, streams) y probablemente no aplican al bundle del navegador (a confirmar). lodash se usa para una sola mezcla de preferencias, de modo que podría eliminarse en lugar de actualizarse.
- Prioridad propuesta: Alta (axios, llamadas de login y con token); Media (lodash y `npm audit` transitivo).
- Contrato potencialmente afectado: `POST /auth/login` y `GET /api/tasks` (misma forma de petición/respuesta; cambia el cliente HTTP). El salto a axios 1.x puede cambiar el manejo de errores/cabeceras.
- Validación ejecutada: `npm ci` (exit 0); OSV para las versiones instaladas (0 advisories); `npm ls axios lodash --depth=0`; `python tools/lab.py test web` (6 passed, build exitoso); `npx tsc --noEmit -p tsconfig.json` (exit 0). Cobertura de login 90% y dashboard 91,17%; el agregado es 77,17%. No se probó el flujo contra servicios reales.

### H-WEB-02 — Token y usuario en `localStorage`, sin expiración ni manejo de 401
- Estado: CANDIDATO
- Evidencia: web/src/app/login/login.component.ts:47-48 (`workshop_token` y `workshop_user` guardados); web/src/app/dashboard/dashboard.component.ts:36-37 (lectura) y :75-76 (borrado). El dashboard solo comprueba que el token exista (:38-41); un token vencido o rechazado cae en el `catch` (:65-71) y solo muestra un mensaje, sin limpiar la sesión ni redirigir a `/login`. Las rutas no tienen guard (web/src/app/app.routes.ts:4-11). Las claves `workshop_*` están repetidas como literales en 8 sitios (login.component.ts:24, 47-49; dashboard.component.ts:36-37, 75-76).
- Impacto: cualquier script que corra en el origen (XSS, dependencia comprometida; ver H-WEB-01 y H-WEB-03) puede leer el token. Sesión caducada deja al usuario atascado en un dashboard con error. `user` se parsea sin proteger `JSON.parse` (dashboard:37), así que un valor corrupto rompe `ngOnInit`.
- Prioridad propuesta: Alta (almacenamiento) / Media (sesión caducada y `JSON.parse`).
- Contrato potencialmente afectado: respuesta de `POST /auth/login` (`token`, `user`) y cabecera `Authorization: Bearer` hacia `/api/tasks`; cualquier alternativa (cookie HttpOnly, memoria) requiere acordarla con `auth`/`api`, no solo con `web`.
- Cómo validarlo: prueba con `localStorage` simulado: token inválido/vencido → se espera limpieza y redirección; `workshop_user` corrupto → no debe lanzar; inspección en DevTools > Application tras login. La alternativa de almacenamiento se decide en revisión (ADR) antes de implementar.

### H-WEB-03 — Mensajes dinámicos con `[innerHTML]` que concatenan usuario y texto del backend
- Estado: CANDIDATO
- Evidencia: web/src/app/login/login.component.html:39 (`[innerHTML]="message"`); web/src/app/login/login.component.ts:34, 37, 52 y 56 (HTML armado con `<strong>`/`<br>`, y en :56 se concatenan `this.username` y `backendMessage`, este último de `error.response.data.message` o `error.message`).
- Impacto: se renderiza HTML construido con entrada del usuario y texto del servidor. El sanitizador de Angular elimina scripts y atributos peligrosos, por lo que no se afirma XSS ejecutable (no probado), pero sí es posible inyectar marcado visual (enlaces, formularios, texto engañoso) en el mensaje de error y se depende del sanitizador como única defensa. Además muestra al usuario el mensaje crudo del backend.
- Prioridad propuesta: Media.
- Contrato potencialmente afectado: textos de error de `POST /auth/login` mostrados en pantalla (campo `message`); el cambio visual de los mensajes debe revisarse con producto.
- Cómo validarlo: prueba de componente con `username` = `<img src=x><a href="https://example.invalid">clic</a>` y comprobar si el DOM resultante contiene esos nodos; tras el cambio, esperar texto plano (`{{ message }}`) y mismos textos funcionales.

### H-WEB-04 — Orden por prioridad invertido: la comparación de cadenas deja `HIGH` al final
- Estado: CANDIDATO
- Evidencia: web/src/app/dashboard/dashboard.component.ts:54 (`tmp.sort((a, b) => a.priority > b.priority ? -1 : 1)`). Comando con datos ficticios `[LOW, HIGH, MEDIUM]` en `node -e`: resultado `MEDIUM,LOW,HIGH` (orden alfabético descendente). El comparador nunca devuelve 0 (inconsistente para prioridades iguales). `docs/ENDPOINTS.md` documenta `HIGH` como prioridad con significado especial en el resumen.
- Impacto: si la intención es mostrar lo más urgente primero, la vista muestra las tareas `HIGH` al final. Es una hipótesis de intención: no hay requisito escrito del orden esperado.
- Prioridad propuesta: Media (defecto funcional visible, bajo riesgo de corrección tras confirmar el orden).
- Contrato potencialmente afectado: orden de presentación de `GET /api/tasks` en el dashboard (la API lo devuelve ordenado por `id`; el orden de pantalla lo decide `web`). No cambia endpoints.
- Cómo validarlo: confirmar con el responsable de producto el orden esperado; prueba unitaria de la función de ordenación con `HIGH`, `MEDIUM`, `LOW`, iguales y valores desconocidos.

### H-WEB-05 — Componentes mezclan HTTP, sesión, URLs y navegación; `any` extendido y cobertura 3,65%
- Estado: CANDIDATO
- Evidencia: URLs fijas en web/src/app/login/login.component.ts:42 (`http://localhost:8080/auth/login`) y web/src/app/dashboard/dashboard.component.ts:43 (`http://localhost:8000/api/tasks?owner=` + valor sin codificar). Los componentes llaman `axios`, `localStorage` y `Router` directamente (login.component.ts:41-50; dashboard.component.ts:36-45, 74-77). `any` en login.component.ts:16-20, 41 y 54 y dashboard.component.ts:23-27, 43, 54 y `formatTaskLabel(task: any)` (web/src/app/utils/legacy-format.ts:1). `if` anidados en login.component.ts:33-60. Mapa `STATUS_LABELS` con claves `RESUELTO` y `COMPLETED` (dashboard.component.ts:10-11) que `docs/ENDPOINTS.md` no lista (valores documentados: `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`). Hay un parche con `NgZone.run` + `detectChanges` manual (dashboard.component.ts:56-62). Cobertura medida con `npx vitest run --coverage`: 3,65% de líneas y sentencias, 22,22% de ramas; `login.component.ts` y `dashboard.component.ts` en 0%; solo existe 1 prueba (web/src/app/utils/legacy-format.spec.ts:5) y `vitest.config.ts:5` usa entorno `node`.
- Impacto: no se puede probar ni cambiar el flujo de login/sesión sin tocar los componentes; esto condiciona la corrección segura de H-WEB-01 a H-WEB-04. URLs fijas impiden cambiar de ambiente (en Compose, el navegador debe alcanzar `localhost:8080/8000`). Sin tipos, un cambio de contrato no se detecta en compilación. Cobertura muy por debajo de la meta del 85% del código modificado.
- Prioridad propuesta: Media (habilitador previo a corregir los demás; escribir pruebas de caracterización primero).
- Contrato potencialmente afectado: `POST /auth/login`, `GET /api/tasks` (la refactorización debe conservarlos tal cual, según `AGENTS.md`), clave `workshop_*` de `localStorage` y valores de estado mostrados en el dashboard.
- Cómo validarlo: `python tools/lab.py test web` (o `npx vitest run --coverage` desde `web/`); escribir pruebas de caracterización de login (éxito, sin token, error con mensaje) y dashboard (sin token, éxito, 401, filtrado `ARCHIVED`) con axios simulado antes de extraer un servicio; confirmar con `docs/ENDPOINTS.md` los estados válidos.

### Pendientes y límites de esta evidencia (web)

- No se ejecutó la aplicación ni se probó contra `auth`/`api` reales (Compose no probado); los hallazgos son de lectura estática más las ejecuciones indicadas.
- Aplicabilidad del resto de advisories de axios que no corresponden al uso examinado en el bundle de navegador no se investigó exhaustivamente.
- Faltan por revisar (no incluidos para evitar ruido): cabeceras de seguridad/CSP en `web/nginx.conf`, accesibilidad del formulario (etiquetas, `aria-live` del mensaje), `console.error(error)` en login.component.ts:57, y `npm audit` de dependencias solo de desarrollo.
- H-WEB-02 a H-WEB-05 continúan como candidatos. La revisión humana de cierre de H-WEB-01 queda pendiente. No se crearon issues.

## auth

Componente `auth` (Quarkus + SQLite). Issue #23; cambio OpenSpec `auth-login-parameterized-queries`. Rama local `feature/h-auth-01`.

### Matriz de seguimiento

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-AUTH-01 | auth | SQL de login concatenado con `username` y `password` | Vulnerabilidad | `LegacyDatabase.findByCredentials` armaba la consulta concatenando los valores recibidos. Un valor como `student'--` o `' OR '1'='1` en la contraseña alteraba la consulta y autenticaba sin credenciales válidas. | auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:32 (código original, commit `3cd6567`) | alta | Resuelto en la rama `feature/h-auth-01`; revisión humana del diff pendiente. `findByCredentials` usa `PreparedStatement` con parámetros `?` (LegacyDatabase.java:17-18, 34-47). Pruebas: `AuthResourceTest` (10). Antes de la corrección fallaban `rejectsSqlInjectionInPassword` y `rejectsSqlCommentInjectionInUsername` (200 en lugar de 401); detalle en `docs/TESTING.md` (sección auth). |

### Pendientes y límites de esta evidencia (auth)

- Contrato de `POST /auth/login` sin cambios. No está documentado en `docs/ENDPOINTS.md`; el baseline es el comportamiento observado.
- Fuera de alcance y sin resolver: contraseñas en texto plano, formato y secreto del token (`LegacyTokenUtil`), mensaje 401 con el `username` recibido, campo `debug` y 401 ante fallo de base de datos.
- No se probó contra `web`/`api` reales (Compose).
- No se hizo push ni integración.
