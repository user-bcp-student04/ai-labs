# Pruebas de contratos HTTP

## auth

Los casos corresponden a los endpoints documentados en
[`ENDPOINTS.md`](./ENDPOINTS.md). Los tests de integración viven en
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`; todos los
casos HTTP ejecutan requests al Quarkus de test, no mocks del transporte.

### Matriz de casos

| endpoint | caso | tipo | resultado esperado |
|---|---|---|---|
| `GET /q/health` | Responde sin comprobaciones configuradas | Camino feliz / borde | `200`, `status=UP`, `checks=[]`. |
| `GET /q/health` | Error del endpoint | No documentado | No hay un error documentado ni una comprobación custom que pueda fallar; no se inventa un resultado esperado. |
| `POST /auth/login` | Cuenta ficticia `student` válida | Camino feliz | `200`, token no vacío, `expiresIn=3600`, username/rol y `debug` esperados. |
| `POST /auth/login` | Campos `username` y `password` solo con espacios | Borde | `400`; mensaje del campo requerido correspondiente. |
| `POST /auth/login` | Request JSON `null` | Error `400` | `{"message":"Request is null"}`. |
| `POST /auth/login` | Username vacío | Error `400` | `{"message":"Username is required"}`. |
| `POST /auth/login` | Password vacía | Error `400` | `{"message":"Password is required"}`. |
| `POST /auth/login` | JSON malformado | Error `400` | Cuerpo vacío, como en el contrato observado localmente. |
| `POST /auth/login` | Content-Type `text/plain` | Error `415` | Cuerpo vacío. |
| `POST /auth/login` | Accept `text/plain` | Error `406` | Cuerpo vacío. |
| `POST /auth/login` | Password incorrecta | Error `401` | `{"message":"Invalid user student or password"}`. |
| `POST /auth/login` | Fallo sintético de base de datos | Error `500` | `{"message":"Authentication service error","exception":"InternalServerError"}`; el detalle sintético no aparece en el cuerpo. |

El código completo y fuente autoritativa de estas pruebas está en el archivo
Java enlazado arriba. Los métodos que cubren directamente los dos endpoints
son:

```java
@Test
void reportsHealthWithoutConfiguredChecks() {
    given()
            .accept("application/json")
            .when().get("/q/health")
            .then()
            .statusCode(200)
            .body("status", is("UP"))
            .body("checks.size()", is(0));
}

@Test
void logsInWithWorkshopUser() {
    given()
            .contentType("application/json")
            .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
            .when().post("/auth/login")
            .then()
            .statusCode(200)
            .body("user.username", is("student"))
            .body("user.displayName", is("Workshop Student"))
            .body("token", notNullValue())
            .body("expiresIn", is(3600))
            .body("user.role", is("STUDENT"))
            .body("debug", is("authenticated-with-legacy-flow"));
}

@Test
void rejectsInvalidCredentials() {
    given()
            .contentType("application/json")
            .body("{\"username\":\"student\",\"password\":\"incorrect-password\"}")
            .when().post("/auth/login")
            .then()
            .statusCode(401)
            .body("message", is("Invalid user student or password"));
}

@Test
void preservesValidationResponsesForMissingLoginFields() {
    given()
            .contentType("application/json")
            .body("null")
            .when().post("/auth/login")
            .then()
            .statusCode(400)
            .body("message", is("Request is null"));

    given()
            .contentType("application/json")
            .body("{\"username\":\"\",\"password\":\"password\"}")
            .when().post("/auth/login")
            .then()
            .statusCode(400)
            .body("message", is("Username is required"));

    given()
            .contentType("application/json")
            .body("{\"username\":\"student\",\"password\":\"\"}")
            .when().post("/auth/login")
            .then()
            .statusCode(400)
            .body("message", is("Password is required"));
}

@Test
void rejectsWhitespaceOnlyLoginFields() {
    given()
            .contentType("application/json")
            .body("{\"username\":\"   \",\"password\":\"password\"}")
            .when().post("/auth/login")
            .then()
            .statusCode(400)
            .body("message", is("Username is required"));

    given()
            .contentType("application/json")
            .body("{\"username\":\"student\",\"password\":\"   \"}")
            .when().post("/auth/login")
            .then()
            .statusCode(400)
            .body("message", is("Password is required"));
}

@Test
void rejectsMalformedJsonWithEmptyBadRequestBody() {
    given()
            .contentType("application/json")
            .body("{bad json")
            .when().post("/auth/login")
            .then()
            .statusCode(400)
            .body(is(""));
}

@Test
void rejectsUnsupportedRequestContentTypeWithEmptyBody() {
    given()
            .contentType("text/plain")
            .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
            .when().post("/auth/login")
            .then()
            .statusCode(415)
            .body(is(""));
}

@Test
void rejectsUnsupportedResponseMediaTypeWithEmptyBody() {
    given()
            .accept("text/plain")
            .contentType("application/json")
            .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
            .when().post("/auth/login")
            .then()
            .statusCode(406)
            .body(is(""));
}

@Test
void returnsGenericErrorWhenAuthenticationFails() {
    LegacyDatabase failingDatabase = new LegacyDatabase() {
        @Override
        void initialize() {}

        @Override
        public UserRecord findByCredentials(String username, String password) {
            throw new IllegalStateException("synthetic-database-failure");
        }
    };
    QuarkusMock.installMockForType(failingDatabase, LegacyDatabase.class);

    given()
            .contentType("application/json")
            .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
            .when().post("/auth/login")
            .then()
            .statusCode(500)
            .body("message", is("Authentication service error"))
            .body("exception", is("InternalServerError"));
}
```

### Ejecución y cobertura

- **Comando:** `mvn verify`
- **Directorio de trabajo:** `auth/`.
- **Entorno:** JDK 21 y DB temporal aislada. Se configuró y ejecutó desde la
  raíz, entrando en el directorio de componente:

  ```powershell
  $env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot'
  $env:Path = "$env:JAVA_HOME\bin;$env:Path"
  $env:AUTH_DB_URL = 'jdbc:sqlite:./data/auth-endpoint-test-20261026.db'
  Push-Location auth
  mvn verify
  ```

  La base temporal se eliminó al terminar.
- **Código de salida:** `0`.
- **Resultado:** `BUILD SUCCESS`; 15 tests, 0 fallos, 0 errores, 0 omitidos.
  El archivo SQLite temporal se eliminó después de la ejecución.
- **Método de cobertura:** JaCoCo 0.8.12 durante `mvn verify`, leyendo
  `auth/target/site/jacoco/jacoco.xml`; cobertura de líneas `covered /
  (covered + missed)` por clase de producción tocada por la solución:
  `AuthResource` 12/12 (100%), `AuthService` 18/18 (100%),
  `LegacyDatabase` 57/67 (85,1%), `PasswordHasher` 39/44 (88,6%) y
  `TokenService` 16/16 (100%). Todas esas clases superan el umbral de 85%.
  No se modificó código de producción en este paso; se añadieron pruebas de
  endpoint.
- **Controles remotos:** CodeQL y Dependency Review no se ejecutaron.

### Fallos

- No hubo fallos en la ejecución descrita.

### Pendientes

- `GET /q/health`: no se documenta una respuesta de error porque el código no
  registra health checks personalizados. La respuesta de un futuro estado
  `DOWN` queda pendiente de contrato y prueba si se añade tal comprobación.
- `POST /auth/login`: el endpoint devuelve actualmente error genérico si falta
  `AUTH_TOKEN_SECRET` al iniciar, pero la aplicación no inicia y por tanto no
  existe una respuesta HTTP que caracterizar para ese caso.
- H-AUTH-03 conserva pendiente el caso en que una contraseña heredada imita la
  forma sintáctica de un hash; esta suite de endpoints no lo cubre. Ver
  `HALLAZGOS.md`.
- H-AUTH-05 conserva pendiente la allowlist CORS y el uso esperado de cookies;
  no se alteró ni se adaptó la prueba HTTP para ocultar esa decisión.

### Pruebas propuestas

- Cuando se defina el comportamiento contractual para health `DOWN`, agregar
  una comprobación local controlada y probar el estado y cuerpo acordados.
- Tras resolver H-AUTH-03, agregar la prueba de regresión de migración de texto
  plano que imita el formato PBKDF2 antes de marcar ese hallazgo como resuelto.
- Tras acordar los orígenes y si se permiten credenciales de navegador,
  caracterizar preflight permitido/no permitido y el encabezado
  `Access-Control-Allow-Credentials` correspondiente.
