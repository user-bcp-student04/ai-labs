## Context

- `POST /auth/login` (`AuthResource.login`) valida la entrada y delega en `LegacyDatabase.findByCredentials(username, password)`. Si devuelve `null` responde 401; si devuelve un `UserRecord` genera el token con `LegacyTokenUtil` y responde 200.
- `findByCredentials` arma el SQL concatenando los valores recibidos:
  `... WHERE username='" + username + "' AND password='" + password + "'"`, y lo ejecuta con `Statement.executeQuery`. Un valor como `' OR '1'='1` cambia la estructura de la consulta y autentica sin credenciales válidas (H-AUTH-01, Issue #23).
- La base es SQLite (`AUTH_DB_URL`, por defecto `jdbc:sqlite:./data/workshop.db`). La tabla `legacy_users` tiene `username` único y `password` en texto plano. `initialize()` crea la tabla y siembra `student` y `trainer`.
- `findByCredentials` captura cualquier excepción, la imprime y devuelve `null`; por eso un fallo de acceso a la base hoy termina en 401.
- La validación del resource usa `trim()` solo para decidir si el campo está vacío; a la consulta llegan los valores originales sin recortar.
- `AuthResourceTest` (QuarkusTest + RestAssured) solo cubre el login válido de `student`.

## Goals / Non-Goals

**Goals**
- Que `username` y `password` se traten siempre como datos en la consulta de credenciales, mediante `PreparedStatement` con parámetros `?` y sin concatenar valores en el SQL.
- Que los intentos de inyección (`' OR '1'='1`, `student'--`) respondan 401 sin `token`.
- Dejar caracterizado el comportamiento actual de `/auth/login` y que `mvn test` pase desde `auth/`.
- Cobertura de 85% o superior en el código modificado.

**Non-Goals**
- Formato, firma o secreto del token (`LegacyTokenUtil`).
- Hash o almacenamiento de contraseñas.
- Refactor de capas o clean code de `AuthResource.login`, mensajes de error o el campo `debug`.
- Las sentencias DDL/seed de `initialize()`: usan SQL constante, sin valores del usuario.
- Cambios en `api`, `web`, `pom.xml` o dependencias.
- Cambiar el 401 ante fallo de base de datos (se conserva el comportamiento observado).

## Contratos protegidos

Baseline: comportamiento observado en `AuthResource` (no hay `/auth/login` en `docs/ENDPOINTS.md`) y los criterios del Issue.

| Entrada | Respuesta que debe conservarse |
|---|---|
| `student` / `Workshop123!` | 200 con `token`, `expiresIn` (3600), `user.username`, `user.displayName`, `user.role` y `debug` |
| `trainer` / `Trainer123!` | 200 con `user.username` = `trainer` |
| Request nulo | 400 con `message` |
| `username` nulo o vacío | 400, `message` = `Username is required` |
| `password` nulo o vacío | 400, `message` = `Password is required` |
| Credenciales sin coincidencia | 401 con `message` (texto actual, incluye el `username`) y sin `token` |
| Excepción inesperada en el resource | 500 con `message` y `exception` |
| Fallo de acceso a base | `findByCredentials` devuelve `null` (401) |

Contratos internos: firma `UserRecord findByCredentials(String, String)`, retorno `null` ante fallo o sin coincidencia, y columnas leídas (`id`, `username`, `display_name`, `role`).

## Componentes afectados

- Modificado: `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`, solo el método `findByCredentials` (y una constante SQL).
- Modificado: `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` (pruebas nuevas).
- Evidencia: fila H-AUTH-01 de `HALLAZGOS.md` y sección `auth` de `docs/TESTING.md`, conservando las secciones de `api` y `web`.
- Sin cambios: `AuthResource`, `LegacyTokenUtil`, `LoginRequest`, `UserRecord`, `pom.xml`, `api/`, `web/`.

## Decisiones técnicas

### D1. `PreparedStatement` con parámetros posicionales
La consulta pasa a ser una constante con nombre:

```
SELECT id, username, display_name, role FROM legacy_users WHERE username = ? AND password = ?
```

`findByCredentials` usa `connection.prepareStatement(SQL)`, asigna `setString(1, username)` y `setString(2, password)` y ejecuta `executeQuery()` dentro del try-with-resources. El mapeo a `UserRecord`, el `catch` y el `return null` no cambian.

Alternativas consideradas:
- **Escapar comillas manualmente**: frágil, depende del dialecto y no cumple el criterio del Issue (`PreparedStatement`). Descartada.
- **Validar o rechazar caracteres especiales en `AuthResource`**: cambia el contrato (400 para contraseñas legítimas con `'`) y no elimina la causa. Descartada.
- **Consulta solo por `username` y comparar la contraseña en Java**: elimina un parámetro pero mueve la lógica de autenticación y se acerca al tema de hash de contraseñas, fuera de alcance. Descartada.
- **ORM / Panache**: dependencia nueva y rediseño no justificado. Descartada.

### D2. Alcance mínimo en una sola clase
Solo cambia el método vulnerable. No se separa en capas ni se renombra nada para que el diff sea revisable y el riesgo de regresión sea acotado.

### D3. Sin cambios en el manejo de errores
El `catch` que imprime y devuelve `null` se mantiene: cambiarlo alteraría el contrato observado (401 ante fallo de base) y pertenece a otro hallazgo.

### D4. Los valores se pasan tal cual
No se aplica `trim()` ni normalización a los valores antes de `setString`, igual que hoy. Una contraseña con espacios no vacíos sigue comparándose literalmente.

## Estrategia incremental

1. **Caracterización**: añadir a `AuthResourceTest` las pruebas de comportamiento válido, inválido y validación de entrada, y confirmar que pasan con el código sin modificar. Commit independiente.
2. **Evidencia de la vulnerabilidad**: añadir las pruebas de inyección y confirmar que `password` = `' OR '1'='1` y `student'--` fallan con el código actual (200 en lugar de 401). La de `username` = `' OR '1'='1` con una `password` cualquiera pasa antes de la corrección, porque `AND` precede a `OR` y la condición resulta falsa; se conserva como prueba de regresión. Commit independiente.
3. **Corrección**: cambiar solo `findByCredentials` (constante SQL + `PreparedStatement`). Todas las pruebas deben pasar sin cambiar sus expectativas.
4. **Validación y evidencia**: `python tools/lab.py test auth` desde la raíz, reporte JaCoCo del código modificado, `git diff` que confirme que no queda concatenación, y actualización de `HALLAZGOS.md` y `docs/TESTING.md`.

Todo en la rama `feature/h-auth-01`, sin push. El orden de las tareas sigue `tasks.md`.

## Pruebas de caracterización necesarias antes de modificar

Se ejecutan sobre el código actual y deben pasar antes de tocar `LegacyDatabase.java`:

- Login válido de `trainer` (200, `user.username` = `trainer`, `token` no nulo); el de `student` ya existe.
- Contraseña incorrecta (`student` / `incorrecta`): 401 sin `token`.
- Usuario inexistente (`noexiste` / `Workshop123!`): 401 sin `token`.
- `username` vacío: 400, `Username is required`.
- `password` vacío: 400, `Password is required`.

Pruebas de inyección (todas deben pasar después de la corrección; las dos últimas fallan antes de ella y la primera es de regresión):

- `username` = `' OR '1'='1`, `password` cualquiera: 401 sin `token`. Pasa ya con el código actual: la consulta queda `username='' OR '1'='1' AND password='...'`, que se evalúa como falsa por la precedencia de `AND`.
- `username` = `student`, `password` = `' OR '1'='1`: 401 sin `token`.
- `username` = `student'--`, `password` cualquiera: 401 sin `token`.

Las pruebas de 401 no verifican el texto de `message`, porque incluye el `username` recibido y su revisión está fuera de alcance. Todas las pruebas deben usar valores de prueba aislados (usuarios sembrados por `initialize()`), sin secretos reales.

## Riesgos / Trade-offs

- **Dependencia de datos sembrados**: las pruebas asumen `student` y `trainer` creados por `initialize()` en la base local `./data/workshop.db`. Mitigación: son los mismos datos que usa la prueba existente; no se modifica el seed.
- **Pruebas rojas intermedias**: el commit de la sección 2 deja la suite en rojo a propósito (dos pruebas). Mitigación: se documenta como evidencia y se corrige en el commit siguiente; no se integra en ese estado.
- **Comportamiento heredado que se mantiene**: contraseñas en texto plano, token débil, mensaje 401 con el `username` y campo `debug` siguen presentes. Mitigación: están listados como fuera de alcance para abrirlos como hallazgos separados.
- **Cobertura**: el método modificado es pequeño, pero la rama del `catch` es difícil de ejercitar sin inyectar un fallo de base. Se reporta la cobertura real de numerador/denominador y método; no se fuerza con cambios de producción.
- **SQLite y `PreparedStatement`**: el driver soporta parámetros `?` con `setString` sin cambios de configuración; el riesgo de incompatibilidad es bajo y lo cubren las pruebas de login válido.

## Rollback

El cambio de producción es un único método en un archivo y los commits son separables. Para revertir basta `git revert` del commit de la corrección (o restaurar `LegacyDatabase.java` a su versión previa); las pruebas de caracterización se conservan y las de inyección volverían a fallar, lo que confirma la vulnerabilidad. No hay migraciones de datos, cambios de esquema, de configuración ni de contrato HTTP, por lo que no se requieren pasos adicionales de despliegue.
