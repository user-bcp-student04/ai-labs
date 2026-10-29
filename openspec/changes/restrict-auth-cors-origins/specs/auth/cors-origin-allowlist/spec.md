# Spec Delta

## Purpose

Define la lista explícita de orígenes de navegador autorizados por CORS para el flujo de autenticación de `auth`, y el control de credenciales por origen.

## ADDED Requirements

### Requirement: Explicit origin allowlist per environment
El servicio `auth` SHALL autorizar CORS únicamente a los orígenes listados explícitamente para cada entorno. Ningún entorno SHALL usar un patrón que acepte cualquier origen.

#### Scenario: Development allowlist contains only the approved origin
- **WHEN** el servicio se ejecuta con el perfil de desarrollo
- **THEN** la lista de orígenes autorizados contiene exactamente `http://localhost:4200`

#### Scenario: Production allowlist is empty until approved
- **WHEN** el servicio se ejecuta con el perfil de producción y no hay orígenes productivos aprobados
- **THEN** ningún origen recibe autorización CORS

#### Scenario: Wildcard origin pattern is not accepted
- **WHEN** se revisa la configuración CORS de `auth` en cualquier perfil
- **THEN** no existe un patrón que acepte cualquier origen (`*` o `/.*/`)

### Requirement: Preflight from an approved origin is granted
Para una solicitud preflight `OPTIONS` dirigida a `POST /auth/login` con cabecera `Origin` igual a un origen aprobado, el servicio SHALL responder con `Access-Control-Allow-Origin` igual a ese origen y con los métodos y cabeceras ya configurados.

#### Scenario: Approved development origin receives CORS grant
- **WHEN** un navegador envía `OPTIONS /auth/login` con `Origin: http://localhost:4200`, `Access-Control-Request-Method: POST` y `Access-Control-Request-Headers: content-type`
- **THEN** la respuesta incluye `Access-Control-Allow-Origin: http://localhost:4200`
- **AND** la respuesta incluye `Access-Control-Allow-Methods` con `POST`
- **AND** la respuesta incluye `Access-Control-Allow-Headers` con `content-type`

### Requirement: Credentials are granted only to approved origins
Para un origen aprobado, el servicio SHALL incluir `Access-Control-Allow-Credentials: true` en las respuestas de `POST /auth/login` y de su preflight. Para cualquier otro origen SHALL NOT incluir esa cabecera.

#### Scenario: Approved origin receives credentials permission
- **WHEN** un navegador envía `OPTIONS /auth/login` con `Origin: http://localhost:4200`
- **THEN** la respuesta incluye `Access-Control-Allow-Credentials: true`

#### Scenario: Credentials are never combined with a wildcard origin
- **WHEN** se evalúa cualquier respuesta de `auth` con `Access-Control-Allow-Credentials: true`
- **THEN** la cabecera `Access-Control-Allow-Origin` contiene un origen concreto y nunca `*`

### Requirement: Non-approved origins receive no CORS grant
Para un origen que no está en la lista aprobada del entorno, el servicio SHALL NOT incluir `Access-Control-Allow-Origin` ni `Access-Control-Allow-Credentials` en la respuesta.

#### Scenario: Unknown origin preflight is not granted
- **WHEN** un navegador envía `OPTIONS /auth/login` con `Origin: https://sitio-no-aprobado.example`
- **THEN** la respuesta no incluye `Access-Control-Allow-Origin`
- **AND** la respuesta no incluye `Access-Control-Allow-Credentials`

#### Scenario: Production with empty allowlist grants no origin
- **WHEN** un navegador envía `OPTIONS /auth/login` con `Origin: http://localhost:4200` al servicio con el perfil de producción
- **THEN** la respuesta no incluye `Access-Control-Allow-Origin`

#### Scenario: Origin match is exact
- **WHEN** un navegador envía `OPTIONS /auth/login` con `Origin: http://localhost:4201` o `Origin: https://localhost:4200`
- **THEN** la respuesta no incluye `Access-Control-Allow-Origin`

### Requirement: Login contract is preserved for CORS-granted and non-browser requests
El cambio de CORS SHALL NOT modificar el contrato de `POST /auth/login` ni el de `GET /q/health`. Las solicitudes sin cabecera `Origin` SHALL mantener su comportamiento actual.

#### Scenario: Valid login from approved origin keeps its response shape
- **WHEN** un navegador con `Origin: http://localhost:4200` envía `POST /auth/login` con credenciales válidas
- **THEN** la respuesta es `200` con los campos `token`, `expiresIn` (3600), `user` y `debug`

#### Scenario: Request without Origin header keeps current behavior
- **WHEN** un cliente sin cabecera `Origin` envía `POST /auth/login` con credenciales válidas
- **THEN** la respuesta es `200` con el mismo contrato que antes del cambio

#### Scenario: Health endpoint is unaffected
- **WHEN** se consulta `GET /q/health`
- **THEN** la respuesta es `200` con `status: UP`
