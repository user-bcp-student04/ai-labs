# Contratos de ReqFlow

Contratos HTTP de cada servicio. Cada sección es de un componente; las de `auth` y `web` se documentan en sus propios pasos y no se tocan desde la sección `api`.

## api

### Cómo leer esta sección

| Tipo | Significado |
|---|---|
| Contrato observado | Lo que hace el código actual de `api/`, comprobado el 2026-11-02 ejecutando la aplicación localmente con una base y un directorio de subidas temporales y datos ficticios. Todos los ejemplos de esta sección son respuestas reales de esa ejecución. |
| Contrato acordado | Decisiones del plan de `PLAN.md` que el usuario aprobó en el chat ("apruebo todos los cambios mencionados", 2026-11-02). No hay un contrato acordado con `auth` ni con `web`. |
| Riesgo pendiente | Lo que sigue abierto; ver la sección final y `HALLAZGOS.md`. |

No hay aprobación humana de cierre de la API registrada.

### Información general

- **URL base**: `http://localhost:8000` (Compose publica `127.0.0.1:8000`; `uvicorn app.main:app`, puerto 8000 en el `Dockerfile`). Documentación interactiva generada por FastAPI en `/docs` y esquema en `/openapi.json`.
- **Formato**: JSON en peticiones y respuestas, salvo la subida de archivos (`multipart/form-data`). Los nombres de campo van en `camelCase` (`createdAt`, `byStatus`, `fileName`).
- **Autenticación**: todos los endpoints exigen el header `Authorization: Bearer <token>`. El token lo emite el servicio de autenticación; el formato que `api` acepta hoy es el legado descrito abajo.
- **Cabecera CORS**: orígenes permitidos por defecto `http://localhost:4200` y `http://127.0.0.1:4200` (configurables con `WORKSHOP_CORS_ORIGINS`, separados por coma); métodos `GET`, `POST`, `OPTIONS`; cabeceras `Authorization` y `Content-Type`; se permiten credenciales.
- **Variables de entorno**: `WORKSHOP_DB_PATH` (por defecto `./data/workshop.db`), `WORKSHOP_UPLOAD_DIR` (`./uploads`), `AUTH_HEALTH_URL` (`http://localhost:8080/q/health`, debe ser `http` o `https`), `WORKSHOP_CORS_ORIGINS`.

#### Token aceptado hoy (formato legado)

El token es el Base64 de `usuario|rol|expiración|secreto`, donde la expiración es un entero en segundos Unix y el secreto es el valor compartido con `auth` (no se publica aquí). Se rechaza si el Base64 es inválido, no tiene exactamente 4 partes, el secreto no coincide o la expiración ya pasó. Del token se toma el `usuario` como identidad; el `rol` se lee pero ningún endpoint lo usa. Este formato no es una firma: ver "Riesgos pendientes" (H-API-02).

#### Errores comunes a todos los endpoints

| Código | Cuándo ocurre | Cuerpo real |
|---|---|---|
| 401 | Falta el header, el token no se puede decodificar, tiene otra forma, el secreto es incorrecto o expiró. El mensaje es el mismo en todos los casos. | `{"detail":"Invalid or expired token"}` |
| 405 | Método no definido para la ruta (por ejemplo `DELETE /api/tasks`). | `{"detail":"Method Not Allowed"}` |
| 500 | Error no controlado. La respuesta no incluye detalles; el detalle va solo al log del servidor. | Texto plano: `Internal Server Error` |

Los errores de validación (422) tienen el formato estándar de FastAPI: `{"detail":[{"type":…,"loc":[…],"msg":…,"input":…}]}`. `input` repite el valor enviado por el cliente.

---

### 1. GET /api/tasks

**1. Qué hace.** Lista las tareas del usuario autenticado, ordenadas por `id` ascendente.

**2. Autenticación.** Obligatoria: `Authorization: Bearer <token>`.

**3. Request.**

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `owner` (query) | string | No | Si se envía, debe coincidir con el usuario del token; cualquier otro valor da 403. Vacío o ausente equivale al usuario del token. |

```http
GET /api/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

```bash
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/tasks"
```

**4. Respuesta exitosa.** `200 OK`, `application/json`: arreglo de tareas (vacío `[]` si el usuario no tiene).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador autoincremental. |
| `title` | string | Título. |
| `description` | string | Descripción (puede ser `""`). |
| `status` | string | Estado. Las tareas creadas por la API usan `TODO`, `IN_PROGRESS`, `DONE` o `ARCHIVED`. |
| `owner` | string | Usuario propietario; siempre el del token. |
| `priority` | string | Prioridad. Las tareas creadas por la API usan `HIGH`, `MEDIUM` o `LOW`. |
| `createdAt` | string | Fecha de creación en UTC, formato `YYYY-MM-DD HH:MM:SS` (generada por SQLite). |

```json
[
  {
    "id": 1,
    "title": "Refactor login",
    "description": "Separar responsabilidades en frontend",
    "status": "TODO",
    "owner": "student",
    "priority": "HIGH",
    "createdAt": "2026-11-02 22:09:09"
  },
  {
    "id": 2,
    "title": "Review API",
    "description": "Revisar seguridad de endpoints",
    "status": "IN_PROGRESS",
    "owner": "student",
    "priority": "MEDIUM",
    "createdAt": "2026-11-02 22:09:09"
  }
]
```

**5. Errores.**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Token ausente, inválido o expirado. | `{"detail":"Invalid or expired token"}` |
| 403 | `owner` distinto del usuario del token (`?owner=trainer` con el token de `student`). | `{"detail":"Access to another owner's data is not allowed"}` |
| 405 / 500 | Ver "Errores comunes". | |

**6. Notas de seguridad.**
- La autorización depende de la identidad del token: la consulta SQL filtra siempre por el usuario del token y parametriza el valor (`?`). El parámetro `owner` ya no permite ver datos de otro usuario.
- Cambio de contrato respecto al comportamiento anterior: antes un `owner` ajeno devolvía las tareas de ese usuario; ahora devuelve 403 (decisión aprobada en `PLAN.md`, H-API-03).
- La confianza en la identidad es tan fuerte como el token (ver H-API-02).

---

### 2. POST /api/tasks

**1. Qué hace.** Crea una tarea a nombre del usuario autenticado.

**2. Autenticación.** Obligatoria: `Authorization: Bearer <token>`. `Content-Type: application/json`.

**3. Request.** Cuerpo JSON:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `title` | string | Sí | De 1 a 200 caracteres. |
| `description` | string | No (por defecto `""`) | Hasta 2000 caracteres. No admite `null`. |
| `status` | string | No (por defecto `TODO`) | Uno de `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`. |
| `priority` | string | No (por defecto `MEDIUM`) | Uno de `HIGH`, `MEDIUM`, `LOW`. |

Cualquier otro campo se ignora, incluido `owner`: el propietario siempre es el usuario del token.

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Write docs","description":"Document the API","status":"IN_PROGRESS","priority":"HIGH","owner":"trainer"}'
```

**4. Respuesta exitosa.** `201 Created`, `application/json`: la tarea creada, con los mismos campos que en `GET /api/tasks`.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador asignado. |
| `title` | string | Título guardado. |
| `description` | string | Descripción guardada. |
| `status` | string | Estado guardado. |
| `owner` | string | Usuario del token (no el `owner` del cuerpo). |
| `priority` | string | Prioridad guardada. |
| `createdAt` | string | Fecha UTC `YYYY-MM-DD HH:MM:SS`. |

Respuesta al request de arriba (el `owner: "trainer"` enviado se ignoró):

```json
{
  "id": 4,
  "title": "Write docs",
  "description": "Document the API",
  "status": "IN_PROGRESS",
  "owner": "student",
  "priority": "HIGH",
  "createdAt": "2026-11-02 22:09:09"
}
```

Con solo `{"title":"Only title"}` se obtiene `"description":""`, `"status":"TODO"`, `"priority":"MEDIUM"`.

**5. Errores.**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Token ausente, inválido o expirado. | `{"detail":"Invalid or expired token"}` |
| 422 | Falta `title`. | `{"detail":[{"type":"missing","loc":["body","title"],"msg":"Field required","input":{}}]}` |
| 422 | `status` o `priority` fuera de los valores permitidos (ejemplo con `"status":"BOGUS"`). | `{"detail":[{"type":"enum","loc":["body","status"],"msg":"Input should be 'TODO', 'IN_PROGRESS', 'DONE' or 'ARCHIVED'","input":"BOGUS","ctx":{"expected":"'TODO', 'IN_PROGRESS', 'DONE' or 'ARCHIVED'"}}]}` |
| 422 | `description` igual a `null`. | `{"detail":[{"type":"string_type","loc":["body","description"],"msg":"Input should be a valid string","input":null}]}` |
| 422 | `title` de más de 200 caracteres, `description` de más de 2000, `title` vacío o tipo incorrecto (mismo formato, con `string_too_long`, `string_too_short` o `string_type`). | Ejemplo para el cuerpo no JSON `nope`: `{"detail":[{"type":"json_invalid","loc":["body",0],"msg":"JSON decode error","input":{},"ctx":{"error":"Expecting value"}}]}` |
| 405 / 500 | Ver "Errores comunes". | |

**6. Notas de seguridad.**
- El `owner` del cuerpo se ignora: no se puede crear una tarea a nombre de otro usuario (antes sí; cambio aprobado en `PLAN.md`, H-API-03).
- El `INSERT` usa parámetros; las comillas en `title` o `description` se guardan como texto literal.
- `status` y `priority` ahora se validan contra una lista; antes se aceptaba cualquier texto (H-API-10, decisión aprobada).
- Un `title` con solo espacios se acepta (ver preguntas abiertas).

---

### 3. GET /api/summary

**1. Qué hace.** Devuelve el resumen de tareas del usuario autenticado: cuántas tiene, cuántas por estado y cuántas de prioridad alta siguen abiertas.

**2. Autenticación.** Obligatoria: `Authorization: Bearer <token>`.

**3. Request.**

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `owner` (query) | string | No | Igual que en `GET /api/tasks`: si se envía debe coincidir con el usuario del token; vacío o ausente equivale al usuario del token. |

```bash
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/summary"
```

**4. Respuesta exitosa.** `200 OK`, `application/json`.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Usuario del token. |
| `total` | integer | Número de tareas del usuario. |
| `byStatus` | objeto (string → integer) | Cantidad de tareas por cada estado presente; solo aparecen los estados con al menos una tarea. |
| `highPriorityOpen` | integer | Tareas con prioridad `HIGH` cuyo estado no es `DONE` ni `ARCHIVED`. |

```json
{
  "owner": "student",
  "total": 4,
  "byStatus": {"TODO": 2, "IN_PROGRESS": 2},
  "highPriorityOpen": 2
}
```

Un usuario sin tareas obtiene `{"owner":"nobody","total":0,"byStatus":{},"highPriorityOpen":0}`.

**5. Errores.**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Token ausente, inválido o expirado. | `{"detail":"Invalid or expired token"}` |
| 403 | `owner` distinto del usuario del token. | `{"detail":"Access to another owner's data is not allowed"}` |
| 405 / 500 | Ver "Errores comunes". | |

**6. Notas de seguridad.**
- Misma regla que `GET /api/tasks`: el resumen se calcula siempre sobre la identidad del token y con consulta parametrizada; un `owner` ajeno da 403 (antes se devolvía el resumen de ese usuario).
- Sin regla de roles: ningún rol puede consultar el resumen de otro usuario.

---

### 4. POST /api/requirements

**1. Qué hace.** Sube un archivo de requerimientos (por ejemplo un `.txt`) y lo guarda en el servidor.

**2. Autenticación.** Obligatoria: `Authorization: Bearer <token>`. `Content-Type: multipart/form-data`.

**3. Request.**

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `file` (parte multipart) | archivo | Sí | Máximo 1 MiB (1 048 576 bytes). Extensión permitida `.txt`, `.md` o `.pdf` (sin distinguir mayúsculas). |

Reglas sobre el nombre del archivo: se toma solo el último segmento (se aceptan `/` y `\` como separadores), se quitan los puntos iniciales y cada carácter fuera de `A-Z a-z 0-9 . _ -` se reemplaza por `_`; si queda vacío o supera 100 caracteres se rechaza. La extensión se valida sobre el nombre ya normalizado. Un archivo con el mismo nombre se sobrescribe sin aviso.

```bash
curl -X POST http://localhost:8000/api/requirements \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@reqs.txt;type=text/plain"
```

**4. Respuesta exitosa.** `201 Created`, `application/json`.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Usuario del token. |
| `fileName` | string | Nombre con el que se guardó, ya normalizado. |
| `storedAt` | string | Igual que `fileName` (no se expone la ruta del servidor). |
| `size` | integer | Tamaño en bytes. |

```json
{"owner": "student", "fileName": "reqs.txt", "storedAt": "reqs.txt", "size": 24}
```

**5. Errores.** El orden de validación es: token, nombre, extensión, tamaño.

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Token ausente, inválido o expirado. | `{"detail":"Invalid or expired token"}` |
| 400 | El nombre queda vacío al normalizarlo (por ejemplo `..`) o supera 100 caracteres. | `{"detail":"Invalid file name"}` |
| 415 | Extensión distinta de `.txt`, `.md` o `.pdf` (por ejemplo `a.exe`). | `{"detail":"File extension not allowed"}` |
| 413 | El archivo supera 1 MiB. No se guarda nada. | `{"detail":"File exceeds the maximum allowed size"}` |
| 422 | Falta la parte `file`. | `{"detail":[{"type":"missing","loc":["body","file"],"msg":"Field required","input":null}]}` |
| 422 | La parte `file` llega con nombre vacío (se interpreta como campo de texto). | `{"detail":[{"type":"value_error","loc":["body","file"],"msg":"Value error, Expected UploadFile, received: <class 'str'>","input":"x","ctx":{"error":{}}}]}` |
| 405 / 500 | Ver "Errores comunes". | |

**6. Notas de seguridad.**
- El nombre enviado por el cliente nunca se usa tal cual: no se puede escribir fuera del directorio de subidas con `../` o `..\`.
- El límite de 1 MiB se valida al leer el contenido; el servidor ya recibió el cuerpo completo antes de responder 413 (H-API-04 sigue pendiente en este punto).
- Todos los usuarios comparten un único directorio: un usuario puede sobrescribir el archivo de otro con el mismo nombre. `owner` en la respuesta solo informa quién subió, no aísla archivos.
- No hay endpoint para descargar ni listar los archivos subidos.

---

### 5. GET /api/backend-health

**1. Qué hace.** Consulta el estado del servicio de autenticación y devuelve el resultado junto con quién lo pidió.

**2. Autenticación.** Obligatoria: `Authorization: Bearer <token>`. No exige rol.

**3. Request.** Sin parámetros ni cuerpo. La URL consultada la define el servidor con `AUTH_HEALTH_URL`; el cliente no puede cambiarla. Espera de hasta 3 segundos por respuesta.

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/backend-health
```

**4. Respuesta exitosa.** `200 OK`, `application/json`. Responde 200 siempre que el token sea válido, incluso si `auth` no está disponible.

| Campo | Tipo | Descripción |
|---|---|---|
| `requestedBy` | string | Usuario del token. |
| `status` | integer | Código HTTP devuelto por `auth`; `0` si no se pudo conectar. |
| `body` | string | Cuerpo devuelto por `auth` (hasta 1000 caracteres) o `Backend unavailable` si no se pudo conectar. |

`auth` disponible:

```json
{"requestedBy": "student", "status": 200, "body": "{\"status\":\"UP\",\"checks\":[]}"}
```

`auth` no disponible (sigue siendo HTTP 200):

```json
{"requestedBy": "student", "status": 0, "body": "Backend unavailable"}
```

**5. Errores.**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Token ausente, inválido o expirado. | `{"detail":"Invalid or expired token"}` |
| 405 / 500 | Ver "Errores comunes". | |

Un fallo de conexión con `auth` no es un error HTTP: se informa con `status: 0` (ver arriba).

**6. Notas de seguridad.**
- Cualquier usuario autenticado puede ejecutarlo; no hay restricción de rol.
- Los mensajes de error de la conexión ya no se devuelven al cliente (solo `Backend unavailable`); el detalle va al log del servidor.
- Si `auth` responde con un error, su cuerpo (hasta 1000 caracteres) sí se reenvía en `body`.
- `AUTH_HEALTH_URL` se valida al arrancar (solo `http` o `https`); la URL no depende de datos del cliente.

---

### Contrato acordado, observado y riesgos pendientes

**Contrato acordado (aprobado en el chat, ver `PLAN.md`)**: 403 si `owner` no es el usuario del token; el `owner` del cuerpo de `POST /api/tasks` se ignora; `status`/`priority` validados y `422` ante datos inválidos; extensiones `.txt`, `.md`, `.pdf` y máximo 1 MiB; `storedAt` solo con el nombre almacenado; mensajes genéricos en el 401 y en `backend-health`; sin restricción de rol en `backend-health`. No hay contrato acordado con `auth` (formato del token) ni con `web`.

**Contrato observado**: lo descrito arriba, incluidos el formato legado del token y que el prefijo `Bearer ` no se exige realmente (ver preguntas abiertas).

**Riesgos pendientes** (ver `HALLAZGOS.md`):
- H-API-02: el token no está firmado y su secreto está en el código; la identidad es forjable. Hasta resolverlo, la autorización por identidad (H-API-03) no es fiable de extremo a extremo.
- H-API-04: el tamaño máximo se aplica tras recibir el archivo completo; los archivos se comparten entre usuarios y se sobrescriben por nombre.
- H-API-05: dependencia transitiva `starlette 0.50.0` con advisories abiertos y `pytest 9.0.2` en desarrollo.

### Preguntas abiertas

1. ¿Qué formato de token emite `auth` en `POST /auth/login`? Esta sección documenta solo lo que `api` acepta; no se leyó `auth`.
2. El header sin el prefijo `Bearer ` (solo el Base64) también se acepta (`GET /api/tasks` devolvió 200). ¿Se exigirá el prefijo cuando se acuerde el nuevo token?
3. ¿Debe rechazarse un `title` formado solo por espacios? Hoy se acepta con 201.
4. ¿`web` depende del texto de `detail` del 401, de `storedAt` o de valores de `status`/`priority` fuera de los listados? No se pudo comprobar.
5. ¿Qué política se aplicará a archivos con el mismo nombre y se aislarán por usuario?
6. ¿Algún rol (por ejemplo `trainer`) debe poder consultar datos de otros usuarios? Hoy ninguno.
7. Una base de datos creada antes del refactor puede contener `status` o `priority` con otros valores; la respuesta los devuelve tal cual (el campo es `string`). No se inspeccionó `api/data/workshop.db`.
