# Contratos HTTP — componente auth

Este documento describe el comportamiento observado del componente `auth`.
Las rutas usan como base local `http://localhost:8080` (README.md); el host
real depende del entorno. Los ejemplos de respuesta son ilustrativos. El token
del ejemplo de login es un marcador porque cada respuesta emite un JWT
distinto; no se debe copiar como credencial.

## `GET /q/health`

### 1. Qué hace

Permite a quien integra o supervisa el servicio comprobar que el endpoint de
salud de autenticación está respondiendo. Ruta habilitada por
`quarkus-smallrye-health` en `auth/pom.xml:35-38`; el README anuncia
`http://localhost:8080/q/health`.

### 2. Autenticación

No requiere autenticación ni un encabezado `Authorization`. No hay recurso
HTTP de salud personalizado en el código de `auth/`.

### 3. Request

No tiene campos ni cuerpo JSON.

| campo | tipo | obligatorio | descripción |
|---|---|---|---|
| — | No aplica | No | Solicitud `GET` sin cuerpo. |

Ejemplo de solicitud:

```http
GET /q/health HTTP/1.1
Host: localhost:8080
Accept: application/json
```

### 4. Response exitosa

**Estado:** `200 OK`.

La respuesta observada localmente con Quarkus 3.27.4 fue:

| campo | tipo | descripción |
|---|---|---|
| `status` | string | Estado agregado del endpoint de salud. |
| `checks` | array de objetos | Comprobaciones registradas por la aplicación; está vacío en la ejecución observada. |

Ejemplo completo observado:

```json
{
  "status": "UP",
  "checks": []
}
```

### 5. Errores

No hay comprobaciones personalizadas de salud en el código de `auth/`, y la
ejecución local respondió `200` con estado `UP`. El código del componente no
define un cuerpo de error para esta ruta. El estado y el cuerpo que se
devolverían si se registra una comprobación que falle no están especificados
por este contrato; confirmar ese caso si se agregan health checks.

### 6. Notas de seguridad

El endpoint no está protegido por autenticación en el comportamiento observado.
No se deben incluir datos sensibles en futuras comprobaciones de salud.

## `POST /auth/login`

### 1. Qué hace

Autentica las credenciales de una cuenta y, si son válidas, devuelve un token
firmado para identificar al usuario. Implementación HTTP:
`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:14-43`;
validación y respuesta de negocio:
`auth/src/main/java/com/bcp/workshop/auth/AuthService.java:23-51`.

### 2. Autenticación

No requiere un token previo ni el encabezado `Authorization`. Requiere
`Content-Type: application/json`. La configuración CORS actual permite todos
los orígenes mediante `/.*/` en
`auth/src/main/resources/application.properties:4-7`; sin embargo, la
comprobación local del preflight no devolvió
`Access-Control-Allow-Credentials: true`. Por tanto, no se debe asumir que
solicitudes de navegador con credenciales/cookies están habilitadas.

### 3. Request

| campo | tipo | obligatorio | descripción |
|---|---|---|---|
| `username` | string | Sí | Nombre de usuario; no puede ser nulo ni vacío o contener solo espacios. |
| `password` | string | Sí | Contraseña; no puede ser nula ni vacía o contener solo espacios. |
| `client` | string | No | Campo aceptado por el DTO, pero no se usa para autenticar ni construir la respuesta. |

La validación está en `auth/src/main/java/com/bcp/workshop/auth/AuthService.java:23-34`;
los campos del DTO, en `auth/src/main/java/com/bcp/workshop/auth/LoginRequest.java:3-6`.
Las propiedades JSON desconocidas se ignoran según
`auth/src/main/resources/application.properties:8`.

Ejemplo:

```http
POST /auth/login HTTP/1.1
Host: localhost:8080
Content-Type: application/json
Accept: application/json

{
  "username": "student",
  "password": "Workshop123!",
  "client": "angular-workshop"
}
```

### 4. Response exitosa

**Estado:** `200 OK`.

Campos definidos por `AuthService.LoginResponse` y `UserResponse`
(`auth/src/main/java/com/bcp/workshop/auth/AuthService.java:47-55,91`):

| campo | tipo | descripción |
|---|---|---|
| `token` | string | JWT firmado; su valor cambia en cada emisión. En este ejemplo se sustituye por un marcador no utilizable. |
| `expiresIn` | integer | Duración en segundos: `3600`. |
| `user` | object | Datos públicos del usuario autenticado. |
| `user.username` | string | Nombre de usuario. |
| `user.displayName` | string | Nombre visible; se escapa con HTML 4 antes de incluirlo en la respuesta. |
| `user.role` | string | Rol asignado a la cuenta. |
| `debug` | string | Valor actual `authenticated-with-legacy-flow`. |

Ejemplo completo de la estructura:

```json
{
  "token": "<JWT HS256 emitido por el servidor; marcador, no reutilizar>",
  "expiresIn": 3600,
  "user": {
    "username": "student",
    "displayName": "Workshop Student",
    "role": "STUDENT"
  },
  "debug": "authenticated-with-legacy-flow"
}
```

### 5. Errores

#### `400 Bad Request` — request nulo

Ocurre cuando el cuerpo JSON es `null`.

```json
{
  "message": "Request is null"
}
```

#### `400 Bad Request` — username faltante o vacío

Ocurre cuando `username` es nulo, vacío o contiene solo espacios.

```json
{
  "message": "Username is required"
}
```

#### `400 Bad Request` — password faltante o vacío

Ocurre cuando `password` es nula, vacía o contiene solo espacios.

```json
{
  "message": "Password is required"
}
```

#### `400 Bad Request` — JSON malformado

El adaptador HTTP de Quarkus devolvió este estado para JSON malformado en la
comprobación local, con cuerpo vacío. No es una respuesta construida por
`AuthResource`; el cuerpo puede depender de la versión/configuración de
Quarkus.

```text
(cuerpo vacío)
```

#### `406 Not Acceptable` — formato de respuesta no aceptado

Ocurre cuando el cliente solicita un formato que no coincide con el producido
por el recurso (`application/json`). En la comprobación local, Quarkus devolvió
el estado con cuerpo vacío.

```text
(cuerpo vacío)
```

#### `415 Unsupported Media Type` — tipo de contenido no admitido

Ocurre cuando el request no usa `Content-Type: application/json`, requerido
por `@Consumes(MediaType.APPLICATION_JSON)` en
`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:14-16`. En la
comprobación local, Quarkus devolvió el estado con cuerpo vacío.

```text
(cuerpo vacío)
```

#### `401 Unauthorized` — credenciales no válidas

Ocurre cuando no existe el usuario o la contraseña no coincide. El mensaje
incluye el username recibido, como se observa en
`auth/src/main/java/com/bcp/workshop/auth/AuthService.java:35-36`.

```json
{
  "message": "Invalid user student or password"
}
```

#### `500 Internal Server Error` — fallo inesperado de autenticación

Ocurre si falla el servicio durante el procesamiento. `AuthResource` registra
el error en el servidor y devuelve un cuerpo genérico
(`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:34-42`).

```json
{
  "message": "Authentication service error",
  "exception": "InternalServerError"
}
```

### 6. Notas de seguridad

- El token es un JWT con firma HMAC-SHA256 (`HS256`) y claims `sub`, `role` y
  `exp`; la expiración configurada es de una hora
  (`auth/src/main/java/com/bcp/workshop/auth/TokenService.java:20-44`).
- La aplicación obtiene el secreto de firma de `AUTH_TOKEN_SECRET` y exige al
  menos 32 bytes; no se debe enviar el secreto al cliente ni guardarlo en el
  repositorio (`TokenService.java:28-35`;
  `auth/src/main/resources/application.properties:9-10`).
- Las contraseñas se almacenan como hashes PBKDF2 con salt y no se devuelven en
  la respuesta (`auth/src/main/java/com/bcp/workshop/auth/PasswordHasher.java:14-56`;
  `AuthService.java:47-55`). La migración de contraseñas heredadas aún tiene un
  caso de formato pendiente identificado en H-AUTH-03; ver `HALLAZGOS.md`.
- CORS está abierto a cualquier origen y la preflight local no autorizó
  credenciales de navegador. La lista de orígenes y el uso de cookies requieren
  una decisión de despliegue; H-AUTH-05 sigue pendiente en `HALLAZGOS.md`.

## Preguntas abiertas

- ¿Qué orígenes CORS exactos deben permitirse por entorno, y se requieren
  cookies o credenciales de navegador? La configuración observada actualmente
  no responde `Access-Control-Allow-Credentials: true`.
- ¿Qué estado/cuerpo debe considerarse contrato cuando una futura comprobación
  de salud devuelva `DOWN`? Actualmente no hay una comprobación personalizada.
- ¿Debe estabilizarse/documentarse el cuerpo vacío que Quarkus devuelve para
  JSON malformado, o basta con garantizar el estado `400`?
