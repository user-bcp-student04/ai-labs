# Proposal

Referencia: Issue [#29](https://github.com/user-bcp-student04/ai-labs/issues/29) — HU-01 (hallazgo H-AUTH-05, componente `auth`).

## Why

La configuración actual de `auth` (`quarkus.http.cors.origins=/.*/` en
`auth/src/main/resources/application.properties:4-7`) acepta solicitudes CORS
desde cualquier origen. Eso permite que un sitio arbitrario lance solicitudes
de navegador contra `POST /auth/login` y consuma sus respuestas. El secreto de
firma ya se obtiene de configuración externa (`AUTH_TOKEN_SECRET`), pero falta
restringir los orígenes. Con la decisión de negocio ya tomada, el cambio
cierra H-AUTH-05 en `HALLAZGOS.md`.

## Decisiones tomadas para este cambio

- Origen aprobado en desarrollo: `http://localhost:4200`.
- Origen aprobado en producción: ninguno por ahora. Sin origen configurado, ningún
  origen recibe autorización CORS en ese entorno.
- Credenciales de navegador (cookies o `Authorization` cross-origin): **habilitadas**
  solo para los orígenes de la lista. Esto cambia el baseline documentado en
  `docs/ENDPOINTS.md` (sección `POST /auth/login` > Autenticación y Notas de
  seguridad), que indica que hoy no se devuelve `Access-Control-Allow-Credentials: true`.

## What Changes

- Sustituir el patrón abierto `/.*/` por una lista explícita de orígenes
  configurable por entorno, con `http://localhost:4200` en desarrollo y lista
  vacía en producción.
- Responder el preflight y las solicitudes del flujo de autenticación con la
  cabecera `Access-Control-Allow-Origin` solo para orígenes de la lista; para
  el resto, no emitir autorización CORS.
- Devolver `Access-Control-Allow-Credentials: true` únicamente a orígenes de la
  lista. Nunca combinar credenciales con comodín `*`.
- Mantener el secreto de firma (`AUTH_TOKEN_SECRET`) fuera del código y sin valor
  por defecto en perfiles no de prueba.
- **BREAKING** para clientes de navegador que no sean `http://localhost:4200`
  (por ejemplo, otros frontends locales o un despliegue web): dejarán de recibir
  autorización CORS hasta que se añadan a la lista aprobada.

## Alcance

Dentro del alcance:
- Configuración CORS de `auth` para el flujo de autenticación (`POST /auth/login`
  y su preflight `OPTIONS`).
- Pruebas de configuración y de preflight que verifican la lista explícita.
- Verificación de que el secreto de firma sigue siendo externo.

Fuera del alcance:
- Cambiar el contrato de `POST /auth/login` (campos de request, forma de la
  respuesta, códigos `400`, `401`, `406`, `415`, `500`).
- Cambiar los métodos (`GET,POST,PUT,DELETE,OPTIONS`) ni la lista de cabeceras
  permitidas (`accept,authorization,content-type,x-requested-with`).
- Migración de contraseñas heredadas (H-AUTH-03), dependencias (H-AUTH-07) y
  refactor de capas (H-AUTH-06).
- Definir orígenes productivos: queda como decisión de despliegue pendiente.
- Cambios en `api/` o `web/`.

## Comportamiento que debe preservarse

- `POST /auth/login` mantiene su contrato: `200` con `token`, `expiresIn` (3600),
  `user` y `debug`; y los errores `400`, `401`, `406`, `415` y `500` con sus cuerpos.
- `GET /q/health` responde `200` con `status: UP` sin autenticación.
- El secreto de firma se obtiene de `AUTH_TOKEN_SECRET`; no se registra ni se
  envía al cliente.
- Una solicitud sin cabecera `Origin` (por ejemplo, `curl`) no cambia de
  comportamiento.

## Capabilities

### New Capabilities
- `auth/cors-origin-allowlist`: lista explícita de orígenes CORS para el flujo de autenticación, con control de credenciales por origen.
- `auth/token-signing-secret`: obtención del secreto de firma solo desde configuración externa, sin valor embebido en perfiles no de prueba.

### Modified Capabilities
- Ninguna. No existen specs previas en `openspec/specs/`; el contrato HTTP de `POST /auth/login` no cambia.

## Impact

- Código: `auth/src/main/resources/application.properties` (configuración CORS y perfiles).
- Pruebas: nuevas pruebas de configuración y de preflight en `auth/src/test/java/`.
- API: solo cambia la autorización CORS para orígenes fuera de la lista.
- Documentación: `docs/ENDPOINTS.md` (CORS y credenciales) y `HALLAZGOS.md` (H-AUTH-05) deberán actualizarse al implementar.
- Dependencias: ninguna nueva.
