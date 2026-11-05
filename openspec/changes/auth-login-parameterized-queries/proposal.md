## Why

El login de `auth` arma la consulta SQL concatenando `username` y `password` (`LegacyDatabase.findByCredentials`). Un valor como `' OR '1'='1` altera la consulta y permite iniciar sesión sin conocer la contraseña, lo que compromete la autenticación de todo el sistema (hallazgo H-AUTH-01, severidad alta).

Fuente del trabajo comprometido: GitHub Issue #23 "H-AUTH-01 Usar consultas parametrizadas en el login de auth".

## What Changes

- Los valores de `username` y `password` recibidos en `POST /auth/login` pasan a tratarse siempre como datos en la consulta de credenciales, nunca como sintaxis SQL. El Issue exige que `findByCredentials` use `PreparedStatement` con parámetros y no concatene valores en el SQL.
- Un intento de inyección SQL en `username` o `password` responde 401 y no devuelve `token`.
- `AuthResourceTest` incorpora pruebas del intento de inyección; `mvn test` debe pasar desde `auth/`.

## Capabilities

### New Capabilities
- `auth-login`: comportamiento verificable de `POST /auth/login`: credenciales válidas, credenciales inválidas, intentos de inyección SQL y validación de entrada.

### Modified Capabilities
(ninguna; no existen specs principales previas)

## Alcance

- Componente `auth` únicamente (`auth/`).
- Consulta de credenciales del login con valores tratados como datos.
- Pruebas automatizadas del intento de inyección en `AuthResourceTest`.

## Fuera de alcance

- Formato, firma y secreto del token (`LegacyTokenUtil`); es un hallazgo distinto.
- Almacenamiento de contraseñas (hoy en texto plano en `legacy_users`).
- Refactor de capas de `AuthResource.login` (clean code), mensajes de error y el campo `debug` de la respuesta.
- Cambios en `api` o `web`.
- Cualquier cambio en el contrato HTTP de `POST /auth/login`.

## Comportamiento que debe preservarse

Baseline: `docs/ENDPOINTS.md` no documenta `/auth/login` (solo contiene la sección `api`). Se toma como baseline el comportamiento observado en `AuthResource` y los criterios del Issue. El Issue no cambia el contrato.

- `student` / `Workshop123!` responde 200 con `token`, `expiresIn` (3600), `user.username`, `user.displayName`, `user.role` y `debug`.
- Request nulo, `username` vacío o `password` vacío responden 400 con `message`.
- Credenciales que no coinciden responden 401 con `message`.
- Un error inesperado responde 500 con `message` y `exception`.

## Impact

- Código afectado: `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java` y `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`.
- Consumidores (`web`, `api`): sin impacto en el contrato.
- Meta de cobertura del código modificado: 85% o superior.

## Supuestos y preguntas abiertas

- Se asume que 401 conserva el mensaje actual, que incluye el `username` recibido; su revisión queda fuera de alcance.
- Si el acceso a la base falla, el comportamiento observado hoy es 401; esta propuesta no lo cambia.