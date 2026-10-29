# Spec Delta

## Purpose

Define cómo `auth` obtiene el secreto de firma de los tokens desde configuración externa, sin valores embebidos fuera de las pruebas y sin exponer su valor.

## ADDED Requirements

### Requirement: Signing secret comes only from external configuration
En los perfiles distintos de prueba, el servicio `auth` SHALL obtener el secreto de firma únicamente desde la variable de entorno `AUTH_TOKEN_SECRET`. No SHALL existir un valor por defecto embebido en el código ni en la configuración de esos perfiles.

#### Scenario: Secret is provided through the environment
- **WHEN** el servicio se ejecuta con el perfil de desarrollo o producción y `AUTH_TOKEN_SECRET` está definido con un valor de al menos 32 bytes
- **THEN** el servicio emite tokens firmados con ese secreto

#### Scenario: Missing secret does not produce tokens
- **WHEN** el servicio se ejecuta con el perfil de desarrollo o producción y `AUTH_TOKEN_SECRET` no está definido
- **THEN** el servicio no emite ningún token
- **AND** no utiliza un secreto de respaldo

#### Scenario: Short secret does not produce tokens
- **WHEN** `AUTH_TOKEN_SECRET` tiene menos de 32 bytes
- **THEN** el servicio no emite ningún token

#### Scenario: No embedded secret is required outside tests
- **WHEN** se revisa la configuración de los perfiles distintos de prueba
- **THEN** ninguna propiedad define un valor literal de secreto de firma

### Requirement: Signing secret is never exposed
El secreto de firma SHALL NOT aparecer en respuestas HTTP, cuerpos de error, logs del servicio ni en el repositorio.

#### Scenario: Login response does not contain the secret
- **WHEN** un cliente envía `POST /auth/login` con credenciales válidas
- **THEN** ni el cuerpo ni las cabeceras de la respuesta contienen el valor de `AUTH_TOKEN_SECRET`

#### Scenario: Error responses do not contain the secret
- **WHEN** ocurre un fallo de autenticación o de configuración del secreto
- **THEN** el cuerpo de la respuesta no contiene el valor del secreto ni detalles de su configuración

### Requirement: Test-only secret value is limited to the test profile
El valor literal de secreto de prueba SHALL usarse únicamente en el perfil de prueba y SHALL NOT estar disponible en los perfiles de desarrollo o producción.

#### Scenario: Test literal is not used outside tests
- **WHEN** el servicio se ejecuta con el perfil de desarrollo o producción sin `AUTH_TOKEN_SECRET`
- **THEN** no utiliza el valor literal definido para pruebas
