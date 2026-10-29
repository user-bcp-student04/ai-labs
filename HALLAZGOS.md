# Hallazgos

## auth

### Contrato observado actualmente de `POST /auth/login`

No existe `docs/ENDPOINTS.md`; por tanto, este contrato se deriva del código y
no representa un acuerdo externo. `POST /auth/login` consume y produce JSON
(`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:14-25`). Las
solicitudes nulas o con campos requeridos vacíos reciben `400`, las
credenciales no válidas reciben `401`, y el login correcto recibe `200` con
`token`, `expiresIn`, `user` y `debug`
(`auth/src/main/java/com/bcp/workshop/auth/AuthService.java:23-40,83-91`).
Los errores internos reciben `500` con valores genéricos en `message` y
`exception`; el detalle se registra del lado servidor
(`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:34-42`). El
request también contiene `client`, que no se usa en este flujo
(`auth/src/main/java/com/bcp/workshop/auth/LoginRequest.java:3-6`).

El registro inicial de discovery describía el comportamiento previo a las
correcciones: el error `500` incluía datos de la excepción y las contraseñas
se comparaban en texto plano. En ese momento no se ejecutaron pruebas; el test
existente solo cubría el login válido.

### Matriz de seguimiento

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-AUTH-01 | auth | Credenciales concatenadas en la consulta SQL | Vulnerabilidad | Antes del cambio, usuario y contraseña se interpolaban en SQL; entradas con sintaxis SQL podían alterar la consulta y el resultado de autenticación. | Antes: `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:32-40`; corrección: `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:111-118` | alta | Resuelto |
| H-AUTH-02 | auth | Token Base64 con secreto embebido y sin firma | Vulnerabilidad | El token anterior exponía el secreto y no acreditaba integridad; ahora se firma con HS256, incluye `sub`, `role` y `exp`, y el secreto se valida al iniciar. | Antes: `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:8,12-15`; corrección: `auth/src/main/java/com/bcp/workshop/auth/TokenService.java:20-44` | alta | Resuelto |
| H-AUTH-03 | auth | Contraseñas guardadas y comparadas en texto plano | Vulnerabilidad | La migración puede confundir una contraseña heredada en texto plano con un hash si su contenido tiene la forma sintáctica PBKDF2; en ese caso la fila se omite y el login deja de funcionar. | `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:88-101`; `auth/src/main/java/com/bcp/workshop/auth/PasswordHasher.java:58-76` | alta | Pendiente |
| H-AUTH-04 | auth | Errores internos expuestos en la respuesta HTTP | Vulnerabilidad | La respuesta `500` anterior incluía el mensaje y el nombre de clase de la excepción; ahora devuelve valores genéricos y registra el detalle solo en el servidor. | Antes: `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:54-58`; corrección: `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:34-42` | media | Resuelto |
| H-AUTH-05 | auth | CORS configurado para cualquier origen | Vulnerabilidad | CORS usaba el patrón `/.*/`, que permitía cualquier origen. Ahora la lista es exacta por perfil: `http://localhost:4200` en desarrollo y vacía en producción; las credenciales se habilitan solo para orígenes aprobados. | Antes: `auth/src/main/resources/application.properties` (`quarkus.http.cors.origins=/.*/`); corrección: `auth/src/main/resources/application.properties`; pruebas `AuthResourceTest` (preflight aprobado y no aprobado) y `ProductionCorsAllowlistTest` | media | Corregido en este Issue, pendiente de revisión |
| H-AUTH-06 | auth | El recurso HTTP combina validación, persistencia, token y respuesta | Refactor | El recurso ahora delega la validación y coordinación del login a `AuthService`, manteniendo el mapeo HTTP en `AuthResource`. | `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:24-31`; `auth/src/main/java/com/bcp/workshop/auth/AuthService.java:23-51` | baja | Resuelto |
| H-AUTH-07 | auth | Versiones de dependencias requieren comprobar advisories | Sugerencia | Quarkus `3.27.4` y Commons Text `1.9` aún requieren una revisión completa de advisories y controles; la versión por sí sola no confirma una vulnerabilidad y los scanners remotos no se ejecutaron. | `auth/pom.xml:13,49`; uso observado de `StringEscapeUtils`: `auth/src/main/java/com/bcp/workshop/auth/AuthService.java:7,51` | baja | Pendiente |
| H-AUTH-08 | auth | Credenciales seed `student`/`trainer` rechazadas tras la siembra | Defecto | El seed se insertaba sin `password_storage`, quedando `LEGACY` por defecto; la migración volvía a aplicar hash sobre el hash ya almacenado. Causa probable, corregida insertando el seed como `HASHED`; en base nueva los 19 tests de `AuthResourceTest` pasan. Las bases creadas antes del fix conservan el valor incorrecto y deben recrearse. | `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java` (`insertSeedUserIfMissing`, `migrateLegacyPasswords`); pruebas `AuthResourceTest` (`logsInWithWorkshopUser`, `returnsSignedTokenWithExplicitClaims`) | pendiente de evaluar | Corregido en este Issue, pendiente de revisión |

**Notas de resolución:** H-AUTH-01 consulta por usuario con `PreparedStatement`
y verifica la contraseña mediante hash, con prueba HTTP para contraseña
ficticia que contiene comilla. H-AUTH-02 usa JWT HS256 con expiración y claims
explícitos; H-AUTH-04 devuelve errores genéricos; H-AUTH-06 separa recurso y
servicio. H-AUTH-03 se reabre porque la detección de hashes de la migración se
basa únicamente en la forma sintáctica y puede saltarse una contraseña
heredada. Las pruebas y la cobertura final se documentan en `PLAN.md`.
H-AUTH-05 queda corregido con la lista de orígenes CORS aprobada, pendiente de revisión;
H-AUTH-07 queda pendiente de revisión completa de dependencias y scanners.
