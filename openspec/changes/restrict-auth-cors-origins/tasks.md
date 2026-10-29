# Tasks

## 1. Caracterización previa al cambio funcional

- [x] 1.1 Agregar una prueba de preflight que documente que, con la configuración actual, un origen arbitrario recibe autorización CORS; verificar el baseline ejecutando `mvn test -Dtest=AuthResourceTest` desde `auth/` y conservar la prueba para invertir su expectativa al restringir la allowlist.
- [x] 1.2 Confirmar antes del cambio que las pruebas existentes de `POST /auth/login` sin `Origin`, sus respuestas y errores, y `GET /q/health` pasan; verificarlo con `mvn test -Dtest=AuthResourceTest` desde `auth/`.

## 2. Allowlist CORS por entorno

- [x] 2.1 Reemplazar la configuración abierta por la lista de desarrollo `http://localhost:4200` y la lista productiva vacía; mantener los métodos y cabeceras actuales y habilitar credenciales explícitamente. Verificar que la configuración de perfiles no contiene comodines y conserva esas listas.
- [x] 2.2 Actualizar la prueba de caracterización y agregar pruebas de preflight para el origen aprobado (origen exacto, métodos, cabeceras y credenciales) y para orígenes no aprobados (sin autorización ni credenciales, incluidos cambios de puerto o esquema); verificar con `mvn test -Dtest=AuthResourceTest` desde `auth/`.
- [x] 2.3 Agregar una prueba de integración bajo el perfil productivo que envíe preflight desde `http://localhost:4200` y confirme que la lista vacía no devuelve autorización CORS; usar solo un secreto de prueba aislado y verificar con la prueba de perfil correspondiente desde `auth/`.
- [x] 2.4 Actualizar únicamente la sección de `auth` en `docs/ENDPOINTS.md` y la entrada H-AUTH-05 en `HALLAZGOS.md` para documentar el origen de desarrollo, las credenciales y la lista productiva vacía; verificar que se conservan las secciones de `api` y `web`.

## 3. Secreto de firma externo

- [x] 3.1 Agregar verificaciones de configuración y pruebas que confirmen que los perfiles no-test obtienen el secreto de `AUTH_TOKEN_SECRET`, que el valor literal de prueba solo se usa en test y que ni respuestas ni logs exponen el secreto; verificar con las pruebas enfocadas de `auth/` sin usar valores reales.

## 4. Verificación de regresión

- [x] 4.1 Ejecutar `python tools/lab.py test auth` desde la raíz y confirmar que las pruebas de CORS, secreto de firma, login y health pasan sin modificar código ni pruebas de `api/` o `web/`.
