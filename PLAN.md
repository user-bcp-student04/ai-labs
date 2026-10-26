# Plan de corrección

## auth

### Alcance y base de compatibilidad

Al elaborar este plan se seleccionaron los siete hallazgos `H-AUTH-01` a
`H-AUTH-07`, entonces marcados `Pendiente`. La sección Decisión registra la
aprobación humana para H-AUTH-02 a H-AUTH-07; H-AUTH-01 ya se había aprobado y
resuelto antes. Tras la implementación y verificación, H-AUTH-02, H-AUTH-04 y
H-AUTH-06 se registran como resueltos. La revisión local reabre H-AUTH-03 por
un caso de migración no cubierto. H-AUTH-05 queda parcialmente corregido y
pendiente de la lista de orígenes CORS; H-AUTH-07 permanece pendiente de
revisión completa de dependencias.

No existe `docs/ENDPOINTS.md`. El contrato observado antes de los cambios, no
acordado, era
`POST /auth/login` con JSON: solicitudes nulas o con usuario/contraseña vacíos
devuelven `400`; credenciales no reconocidas devuelven `401`; el login correcto
devuelve `200` con `token`, `expiresIn`, `user` y `debug`. El error capturado
devuelve `500` con `message` y `exception`. Evidencia:
`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:15-17,22-24,26-58`.
Las pruebas actuales solo verifican el login válido en
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:12-21`.

Antes de cada cambio se agregarán pruebas de caracterización al test de
integración existente o pruebas locales del repositorio/utilidad según el
hallazgo. Los resultados se registrarán solo después de ejecutarlos. La
refactorización conservará endpoint, códigos de estado y forma de la respuesta
exitosa. El cambio de mensajes internos del error `500` de `H-AUTH-04` necesita
aprobación explícita: se propone conservar el estado y las claves JSON, pero
sustituir los valores dinámicos por valores genéricos para no exponer detalles.

### H-AUTH-01 — Credenciales concatenadas en SQL

- **Hallazgo:** `HALLAZGOS.md`, H-AUTH-01, Contrato acordado.
- **Problema:** `LegacyDatabase.findByCredentials` concatena las entradas en el
  `SELECT` y lo ejecuta con `Statement`; la sintaxis recibida puede alterar la
  consulta y el resultado de autenticación.
- **Cambio propuesto:** reemplazar la consulta por `PreparedStatement` con
  marcadores posicionales y enlazar usuario y contraseña mediante parámetros.
  Mantener los mismos campos consultados y el resultado actual para credenciales
  válidas/no válidas.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`;
  `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` y, si se
  necesita aislar el acceso JDBC, un test de repositorio bajo
  `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes del cambio:** probar por HTTP credenciales válidas
  (`200`, usuario y token), inválidas (`401`) y una entrada ficticia con comilla
  simple (`401` según el flujo de error observado). Añadir una prueba de
  repositorio que, tras la corrección, verifique consulta preparada y valores
  enlazados; no usar una prueba de evasión de autenticación.
- **Compatibilidad/pendientes:** el contrato de HTTP no cambia. El test de
  comilla fija el resultado observable antes del cambio; la verificación de
  JDBC preparado es una aserción posterior de remediación.
- **Ejecuciones (componente `auth`, H-AUTH-01; 2026-10-26):**
  - Antes del cambio, `mvn "-Dtest=AuthResourceTest#logsInWithWorkshopUser+rejectsInvalidCredentials+rejectsCredentialsContainingQuoteWhenTheyDoNotMatch" test`
    terminó correctamente: 3 tests, 0 fallos. Maven usó JDK 25 por `JAVA_HOME`;
    JaCoCo 0.8.12 informó que no soporta ese bytecode, así que esta ejecución
    no se considera una comprobación limpia de cobertura.
  - Antes del cambio, `mvn "-Dtest=AuthResourceTest#logsInWhenPasswordContainsQuote" test`
    falló como se esperaba para la corrección: el test esperaba `200` para el
    usuario ficticio almacenado con una contraseña válida que contiene comilla,
    pero recibió `401`. También se registró la incompatibilidad de JaCoCo con
    JDK 25.
  - Después del cambio, `mvn "-Dtest=AuthResourceTest" test` terminó
    correctamente: 4 tests, 0 fallos; se ejecutó con JDK 25 y también produjo
    avisos de instrumentación de JaCoCo.
  - `mvn clean verify`, con JDK 21, no llegó a ejecutar tests: Maven no pudo
    borrar `auth/target/workshop-auth-backend-dev.jar` porque otro proceso lo
    mantenía abierto. No se detuvo ese proceso.
  - Verificación final después del cambio:
    `mvn verify`, desde `auth/` con
    `JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot`,
    terminó con `BUILD SUCCESS`: 4 tests, 0 fallos. JaCoCo para
    `LegacyDatabase`: líneas 21/24 (87.5%), instrucciones 94/100, métodos
    4/4. La cobertura de líneas del código modificado supera la meta de 85%.
  - CodeQL y Dependency Review remotos: no ejecutados en este recorrido local.
- **Resultado:** H-AUTH-01 se marca `Resuelto` en `HALLAZGOS.md`. No se
  implementaron otros hallazgos. La prueba de una contraseña válida almacenada
  con comilla cambia de `401` antes del fix a `200` después: se registra como
  corrección intencional de la interpretación literal de credenciales, no como
  cambio del endpoint ni de su formato de respuesta.

### H-AUTH-02 — Token Base64 sin firma

- **Hallazgo:** `HALLAZGOS.md`, H-AUTH-02, Contrato acordado.
- **Problema:** el token se forma como texto con los datos y el secreto, y solo
  se codifica en Base64; no hay firma criptográfica verificable.
- **Cambio propuesto:** adoptar un token firmado con expiración y claims
  explícitos, manteniendo el campo `token` como string opaco y `expiresIn` en la
  respuesta. Antes de elegir biblioteca, revisar las opciones ya disponibles
  en Quarkus y justificar cualquier dependencia nueva; no añadir una sin
  revisión de licencia, mantenimiento y advisories.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java`;
  `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java` solo si el
  contrato de creación lo requiere; `auth/pom.xml` solo si una dependencia
  aprobada resulta necesaria; pruebas bajo
  `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes del cambio:** ampliar el test de login correcto para
  fijar `200`, las claves y tipos de respuesta (`token`, `expiresIn`, `user`,
  `debug`), y las pruebas de login inválido para `401`. Registrar el valor
  observado de `expiresIn` (actualmente 3600) sin cambiarlo en esta etapa.
- **Compatibilidad/pendientes:** conservar formato externo del login y la
  condición de expiración observada. La representación interna del token
  cambiará; consumidores que interpreten el formato Base64 deben revisarse antes
  de aprobar la implementación. No se ha comprobado aquí ningún consumidor.

### H-AUTH-03 — Contraseñas en texto plano

- **Hallazgo:** `HALLAZGOS.md`, H-AUTH-03, Contrato acordado.
- **Problema:** el esquema y las cuentas iniciales guardan la contraseña legible,
  y la autenticación la compara directamente.
- **Cambio propuesto:** almacenar y verificar hashes lentos con salt. Definir
  antes una migración idempotente y transaccional de las filas existentes, para
  mantener las cuentas y permitir el login tras actualizar una base ya creada;
  no limitar la solución a cambiar solo las filas semilla ni recrear la base.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`;
  una utilidad de hash en `auth/src/main/java/com/bcp/workshop/auth/` si hace
  falta; `auth/pom.xml` únicamente si se justifica y aprueba una dependencia;
  pruebas de integración y persistencia bajo
  `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes del cambio:** fijar mediante HTTP que las cuentas
  semilla actuales autentican con `200` y que contraseña incorrecta devuelve
  `401`. Preparar una prueba con una base SQLite temporal que contenga una fila
  de formato previo y verificar la continuidad del login después de la
  migración; esa aserción de migración es una prueba de remediación, no un
  resultado ya comprobado.
- **Compatibilidad/pendientes:** mantener usuarios, roles y respuestas del
  login. Acordar la estrategia de actualización de bases locales existentes y
  de credenciales almacenadas antes de implementar.

### H-AUTH-04 — Detalles internos en errores HTTP

- **Hallazgo:** `HALLAZGOS.md`, H-AUTH-04, Contrato acordado.
- **Problema:** la respuesta `500` contiene el mensaje de la excepción y su
  nombre de clase, datos que pueden revelar internals.
- **Cambio propuesto:** devolver un mensaje genérico y registrar el detalle solo
  en el servidor mediante logging controlado. Conservar el estado `500` y las
  claves JSON `message` y `exception`, con valores estables que no incluyan la
  excepción original.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java`;
  `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`.
- **Caracterización antes del cambio:** probar el manejo de error inyectando
  una dependencia de prueba que lance una excepción ficticia; fijar el estado
  `500` y las claves/respuesta actuales antes de cambiarla. Después verificar
  que el mensaje y la clase ficticios no aparecen en HTTP y que el evento se
  registra en el servidor.
- **Compatibilidad/pendientes:** el comportamiento observado contiene
  deliberadamente valores dinámicos; sustituirlos cambia esos valores. Se
  requiere aprobación humana de esta excepción de seguridad antes del cambio.
  No se deben volcar stacktraces ni contraseñas en logs.

### H-AUTH-05 — Secreto embebido y CORS abierto

- **Hallazgo:** `HALLAZGOS.md`, H-AUTH-05, Contrato acordado.
- **Problema:** el secreto está en código y la configuración CORS usa un patrón
  que permite cualquier origen.
- **Cambio propuesto:** leer el secreto desde configuración externa, fallar de
  forma explícita si falta en un entorno que firma tokens y usar valores
  ficticios aislados en tests. Restringir CORS a una lista explícita de orígenes
  aprobados; no inventar la lista.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java`;
  `auth/src/main/resources/application.properties`; configuración de test en
  `auth/src/test/resources/` si se necesita; pruebas bajo
  `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes del cambio:** caracterizar login correcto y
  `expiresIn`; probar el preflight CORS actual y luego, tras la decisión de
  orígenes, verificar que un origen aprobado se permite y uno no aprobado se
  rechaza. Usar únicamente un secreto ficticio de test.
- **Compatibilidad/pendientes:** confirmar con quien mantiene el despliegue los
  orígenes necesarios antes de cerrar la lista. No leer ni inferir rutas del
  componente web dentro de este alcance. La disponibilidad de `POST /auth/login`
  y el formato de la respuesta se conservan.

### H-AUTH-06 — Responsabilidades mezcladas en el recurso

- **Hallazgo:** `HALLAZGOS.md`, H-AUTH-06, Contrato acordado.
- **Problema:** `AuthResource.login` valida, llama a persistencia, genera el
  token y construye respuestas en un método anidado, lo que acopla HTTP y
  negocio y dificulta probar responsabilidades por separado.
- **Cambio propuesto:** separar Resource (HTTP), Service (validación/reglas y
  coordinación) y Repository (SQLite); mantener `LegacyDatabase` como
  repositorio durante el primer corte si evita un cambio nominal sin valor.
  Usar retornos anticipados y métodos con una sola responsabilidad, sin
  duplicar validaciones ni usar valores mágicos.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java`;
  nuevo `auth/src/main/java/com/bcp/workshop/auth/AuthService.java`; posiblemente
  `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java` solo para
  ajustar el límite de persistencia; pruebas bajo
  `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes del cambio:** ampliar primero `AuthResourceTest` para
  requests nulos/campos vacíos (`400`), credenciales incorrectas (`401`) y
  correctas (`200` con el mismo conjunto de claves y datos de usuario).
- **Compatibilidad/pendientes:** separar en cambios revisables y mantener
  `POST /auth/login`, estados HTTP y formato de respuestas observados. Coordinar
  el orden con H-AUTH-01 a H-AUTH-05 para evitar mezclar cambios de seguridad
  con arquitectura.

### H-AUTH-07 — Dependencias sin revisión de advisories

- **Hallazgo:** `HALLAZGOS.md`, H-AUTH-07, Contrato acordado; el hallazgo es una
  comprobación pendiente, no una vulnerabilidad confirmada.
- **Problema:** el proyecto fija Quarkus `3.27.4` y Commons Text `1.9`, pero
  todavía no consta una revisión de advisories aplicables.
- **Cambio propuesto:** consultar advisories oficiales y ejecutar los controles
  de dependencias disponibles, coordinando resultados con el responsable de
  dependencias. Solo proponer actualizar o retirar una dependencia cuando la
  evidencia confirme el riesgo y exista una versión compatible. No silenciar
  CodeQL ni Dependency Review y no añadir exclusiones.
- **Archivos a tocar:** `auth/pom.xml` solo si el análisis justifica una
  actualización/remoción; pruebas de integración existentes bajo
  `auth/src/test/java/com/bcp/workshop/auth/` para verificar el login después
  del cambio.
- **Caracterización antes del cambio:** ejecutar y registrar el test de login
  válido e inválido antes de cualquier modificación de dependencias; guardar
  también el árbol/versiones resueltos y el resultado del scanner como evidencia
  de análisis, no como sustituto de la prueba funcional.
- **Compatibilidad/pendientes:** no hay advisory confirmado en este plan. No
  ejecutar actualizaciones a ciegas; preservar el contrato de login y volver a
  ejecutar las pruebas y gates existentes tras cualquier cambio aprobado.

## Secuencia propuesta

1. Acordar la caracterización de `POST /auth/login` y añadir primero sus casos
   de respuesta válida, inválida y de validación.
2. Revisar advisories de H-AUTH-07 y coordinar dependencias candidatas antes de
   decidir cambios al POM.
3. Tratar SQL, migración de contraseñas, token/configuración y errores en
   cambios revisables separados; obtener antes las decisiones externas
   indicadas en H-AUTH-03, H-AUTH-04 y H-AUTH-05.
4. Separar capas en H-AUTH-06 tras caracterizar el flujo, sin mezclarla con la
   sustitución de mecanismos de seguridad.
5. Ejecutar regresión y medir cobertura del código modificado; no registrar
   resultados hasta ejecutar las pruebas con el entorno de `auth`.

Cuando se elaboró este plan no se habían ejecutado pruebas ni scanners. El
comando documentado por el repositorio es `python tools/lab.py test auth` desde
la raíz; las pruebas directas del módulo se ejecutan desde `auth/`.

## Decisión
- Se aprueba H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06 y H-AUTH-07

## Implementación y verificación

Las pruebas de caracterización para token, migración de contraseñas, error
interno y validación del recurso se añadieron y ejecutaron antes de cambiar
esas rutas, según el trabajo registrado en esta sesión. Las salidas detalladas
de esas ejecuciones previas no quedaron copiadas a este plan; no se atribuye
aquí un resultado previo que no pueda citarse. La suite final sí se ejecutó y
se registra abajo. No se modificó el contrato externo observado de
`POST /auth/login`: se mantuvieron `400`, `401`, `200`, la respuesta exitosa y
los campos JSON; H-AUTH-04 reemplazó intencionalmente el contenido dinámico del
error `500` por valores genéricos, conservando el estado y las claves.

### H-AUTH-02 — Resultado

- **Diff:** se reemplazó el token Base64 sin firma por `TokenService`, que emite
  JWT compacto HS256 con `sub`, `role` y `exp`; el secreto se exige por
  configuración y se valida al inicializar.
- **Caracterización antes:** se fijó la respuesta exitosa de login, incluyendo
  `token` y `expiresIn=3600`; la salida individual previa no quedó preservada
  en este documento.
- **Corrección después:** `returnsSignedTokenWithExplicitClaims` comprueba
  formato, algoritmo, claims, expiración y firma. Pasó en la suite final.
- **Estado:** resuelto. No se añadió una dependencia de JWT.

### H-AUTH-03 — Resultado

- **Diff:** se incorporó PBKDF2-HMAC-SHA256 con salt aleatorio y comparación
  constante. La inicialización migra contraseñas heredadas dentro de una
  transacción y la migración es idempotente.
- **Caracterización antes:** se añadieron casos de login válido e inválido y
  continuidad para una fila previa en texto plano; su salida individual no
  quedó preservada en este documento.
- **Corrección después:** `preservesLoginForExistingPlaintextCredentials`
  verifica login después de migrar, hash persistido y estable tras una segunda
  inicialización; `passwordHashesUseUniqueSaltsAndRejectMalformedValues`
  verifica salts distintos y rechaza hashes inválidos. Pasaron en la suite
  final.
- **Revisión local:** la migración decide que una contraseña ya está hasheada
  mediante `PasswordHasher.isHashed`, que comprueba la estructura del valor
  (`auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:88-101`;
  `auth/src/main/java/com/bcp/workshop/auth/PasswordHasher.java:58-76`).
  Una contraseña heredada cuyo texto tenga accidentalmente o deliberadamente
  esa forma sintáctica se omite de la migración; luego se compara como hash y
  no autentica con el valor original. No hay prueba para este caso. H-AUTH-03
  vuelve a `Pendiente` hasta resolver la identificación inequívoca del formato
  almacenado y añadir una prueba de regresión.
- **Estado:** pendiente de corrección y prueba de regresión para el caso de
  colisión de formato.

### H-AUTH-04 — Resultado

- **Diff:** `AuthResource` registra la excepción en el servidor y responde
  `500` con `message` y `exception` genéricos.
- **Caracterización antes:** se añadió una dependencia de prueba que lanza una
  excepción ficticia para fijar el comportamiento HTTP anterior; su salida
  individual no quedó preservada en este documento.
- **Corrección después:** `returnsGenericErrorWhenAuthenticationFails`
  verifica el estado y los valores genéricos, sin filtrar el mensaje ni la
  clase ficticia. Pasó en la suite final.
- **Estado:** resuelto. El log de prueba muestra el error sintético en el
  servidor, no en la respuesta HTTP.

### H-AUTH-05 — Resultado parcial

- **Diff:** el secreto de firma ahora se obtiene de `AUTH_TOKEN_SECRET`, con un
  secreto ficticio limitado al perfil de test. La lista CORS no se cambió.
- **Pendiente:** la configuración sigue permitiendo cualquier origen
  (`quarkus.http.cors.origins=/.*/`). No se inventó una allowlist; H-AUTH-05 no
  se marca resuelto hasta que se acuerden los orígenes.
- **Estado:** pendiente de decisión externa sobre orígenes CORS.

### H-AUTH-06 — Resultado

- **Diff:** `AuthResource` conserva el límite HTTP y delega la validación y
  coordinación a `AuthService`; la persistencia y firma siguen en sus
  respectivas clases.
- **Caracterización antes:** se añadieron casos de request nulo/campos vacíos,
  credenciales inválidas y válidas. La salida individual previa no quedó
  preservada en este documento.
- **Corrección después:** `preservesValidationResponsesForMissingLoginFields`,
  `rejectsInvalidCredentials` y `logsInWithWorkshopUser` pasaron en la suite
  final.
- **Estado:** resuelto.

### H-AUTH-07 — Resultado

- No se cambió la versión de dependencias ni se silenció ningún control.
  La revisión consultada de Commons Text señala un advisory relacionado con
  `StringSubstitutor` y entrada no confiable; el código observado usa
  `StringEscapeUtils`, por lo que esa referencia no confirma por sí sola un
  problema explotable en este flujo.
- CodeQL y Dependency Review remotos no se ejecutaron. La revisión completa de
  advisories y los quality gates remotos siguen pendientes.
- **Estado:** pendiente; no se confirmó una vulnerabilidad ni se justificó
  actualizar dependencias.

### Verificación final común — H-AUTH-01, H-AUTH-02, H-AUTH-04 y H-AUTH-06

- **Comando:** desde la raíz se configuró `JAVA_HOME` a
  `C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot` y
  `AUTH_DB_URL=jdbc:sqlite:./data/review-auth-20261026.db`; con cwd `auth/` se ejecutó
  `mvn verify`.
- **Resultado:** `BUILD SUCCESS`; 10 tests, 0 fallos, 0 errores, 0 omitidos.
  La base SQLite aislada creada para la prueba se eliminó después.
- **JaCoCo, cobertura de líneas:** `AuthResource` 100% (12/12),
  `AuthService` 100% (18/18), `LegacyDatabase` 85,1% (57/67),
  `PasswordHasher` 88,6% (39/44) y `TokenService` 100% (16/16). Los archivos
  de producción modificados superan el umbral de 85%. Esta medición no cubre
  el caso de colisión de formato detectado en la revisión; por eso no basta
  para cerrar H-AUTH-03.
- **Calidad:** `git diff --check` terminó sin errores. `mvn clean verify`
  había fallado anteriormente antes de ejecutar tests porque otro proceso
  mantenía abierto el JAR de desarrollo; no se detuvo ese proceso. El
  `mvn verify` final, sin `clean`, sí completó.
- **Controles no ejecutados:** CodeQL y Dependency Review remotos.

### Desviaciones y pendientes

- H-AUTH-05 se implementó parcialmente (secreto externalizado), pero se dejó
  CORS intacto porque falta la lista aprobada de orígenes.
- H-AUTH-07 no produjo cambios de dependencias: faltan los scanners y una
  revisión completa de advisories. No se silenciaron gates.
- La revisión local reabrió H-AUTH-03: la suite pasa, pero no prueba el caso
  en que texto plano heredado imita la estructura sintáctica de un hash.
- No se creó `docs/ENDPOINTS.md` ni `docs/TESTING.md`, conforme a la instrucción
  de esperar sus pasos de documentación.