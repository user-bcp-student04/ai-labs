## 1. Pruebas de caracterización (sin cambiar código de producción)

- [x] 1.1 Confirmar que la rama actual es `feature/h-auth-01` y que `git status` no muestra cambios ajenos al alcance (excepción aprobada: `.vscode/mcp.json` queda local sin commit por ser configuración de `github-local`, y los skills de `.agents/` y `.github/` siguen sin versionar; ninguno afecta a `auth/`)
- [x] 1.2 En `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`, añadir prueba de login válido de `trainer` / `Trainer123!` (200, `user.username` = `trainer`, `token` no nulo)
- [x] 1.3 Añadir prueba de contraseña incorrecta (`student` / `incorrecta`): 401 y cuerpo sin `token`
- [x] 1.4 Añadir prueba de usuario inexistente (`noexiste` / `Workshop123!`): 401 y cuerpo sin `token`
- [x] 1.5 Añadir prueba de `username` vacío: 400 y `message` = `Username is required`
- [x] 1.6 Añadir prueba de `password` vacío: 400 y `message` = `Password is required`
- [x] 1.7 Ejecutar `python tools/lab.py test auth` desde la raíz y confirmar que las pruebas 1.2 a 1.6 y la existente (`student`) pasan sobre el código sin modificar
- [x] 1.8 Commit de las pruebas de caracterización, sin tocar `LegacyDatabase.java`

## 2. Pruebas del intento de inyección (evidencia de H-AUTH-01)

- [x] 2.1 Añadir prueba con `username` = `' OR '1'='1` y una `password` cualquiera: espera 401 y cuerpo sin `token`
- [x] 2.2 Añadir prueba con `username` = `student` y `password` = `' OR '1'='1`: espera 401 y cuerpo sin `token`
- [x] 2.3 Añadir prueba con `username` = `student'--` y una `password` cualquiera: espera 401 y cuerpo sin `token`
- [x] 2.4 No asertar el texto de `message` del 401 en estas pruebas (incluye el `username` recibido; fuera de alcance)
- [x] 2.5 Ejecutar `python tools/lab.py test auth` y registrar que 2.2 y 2.3 fallan con el código actual (200 en lugar de 401), que 2.1 pasa (la precedencia de `AND` sobre `OR` hace falsa la condición; queda como regresión) y que las de la sección 1 siguen pasando
- [x] 2.6 Commit de las pruebas de inyección, indicando en el mensaje que fallan hasta aplicar la corrección

## 3. Implementación incremental

- [x] 3.1 En `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`, definir el SQL de credenciales como constante con nombre y parámetros `?` para `username` y `password`
- [x] 3.2 En `findByCredentials`, reemplazar `Statement` por `PreparedStatement` y asignar los valores con `setString(1, username)` y `setString(2, password)`, sin concatenar valores en el SQL ni aplicar `trim()`
- [x] 3.3 Conservar la firma de `findByCredentials`, el mapeo a `UserRecord`, el `catch` existente y el retorno `null` ante fallo o sin coincidencia
- [x] 3.4 Confirmar con `git diff` que solo cambió `findByCredentials` (y la constante SQL) y que no se tocaron `AuthResource`, `LegacyTokenUtil`, `initialize()` ni `pom.xml`

## 4. Validación

- [x] 4.1 Ejecutar `python tools/lab.py test auth` desde la raíz: pasan todas las pruebas, incluidas 2.1 a 2.3, sin cambiar las expectativas de la sección 1
- [x] 4.2 Revisar el reporte JaCoCo de `auth/` y registrar numerador, denominador y método de la cobertura del código modificado (meta: 85% o superior); si el `catch` queda sin cubrir, anotarlo sin forzarlo con cambios de producción
- [x] 4.3 Verificar que `git diff` de `LegacyDatabase.java` ya no concatena `username` ni `password` en el SQL
- [x] 4.4 Verificar el contrato protegido: la respuesta 200 de `student` conserva `token`, `expiresIn` (3600), `user.username`, `user.displayName`, `user.role` y `debug`

## 5. Evidencia y cierre

- [x] 5.1 Actualizar la fila H-AUTH-01 de `HALLAZGOS.md` con la evidencia real, conservando las filas de `api` y `web`
- [x] 5.2 Añadir en `docs/TESTING.md` la sección `auth` con comandos, resultados, pruebas añadidas y cobertura, conservando las secciones de `api` y `web`
- [x] 5.3 Commit de la corrección y de la evidencia en `feature/h-auth-01`, sin push
- [x] 5.4 Solicitar la revisión humana del diff antes de cualquier integración
