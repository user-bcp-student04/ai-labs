# Design

## Context

Ver [proposal.md](./proposal.md) para la motivación y
[las specs](./specs/auth/) para los requisitos observables.

- `auth` usa Quarkus 3.27.4 y mantiene su configuración HTTP en
  `auth/src/main/resources/application.properties`.
- El filtro CORS de Quarkus está habilitado globalmente y actualmente usa
  `/.*/`. Los métodos y cabeceras permitidos son listas explícitas. El filtro
  evalúa las solicitudes en la capa HTTP antes de que lleguen al recurso REST;
  no hay lógica CORS en `AuthResource`.
- El flujo `/auth/login` y `GET /q/health` están cubiertos parcialmente por
  `AuthResourceTest`; sus pruebas existentes ejercitan login sin `Origin`,
  respuestas de autenticación y health, pero no caracterizan preflight.
- `TokenService` consume `auth.token.secret` y valida que tenga al menos 32
  bytes. La propiedad apunta a `AUTH_TOKEN_SECRET`; el valor literal actual
  está limitado al perfil `%test`.

## Goals / Non-Goals

**Goals:**

- Implementar las dos capacidades aprobadas usando el filtro CORS existente y
  sin añadir dependencias.
- Aplicar la allowlist globalmente en el componente `auth`: el origen de
  desarrollo aprobado es `http://localhost:4200`; producción empieza sin
  orígenes aprobados. Habilitar credenciales solo junto con una coincidencia
  de origen exacta.
- Preservar métodos y cabeceras CORS actuales, el contrato HTTP de login y el
  uso externo del secreto de firma.
- Mantener verificables por pruebas los perfiles y el comportamiento en tiempo
  de ejecución.

**Non-Goals:**

- Añadir CORS específico por ruta, cambiar recursos HTTP o modificar la
  autenticación y la emisión de tokens.
- Ampliar la lista productiva por anticipado, cambiar `api/` o `web/`, o
  modificar requisitos de cookies/sesión fuera de la decisión ya aprobada.
- Reestructurar `AuthResource`, `AuthService` o `TokenService`.

## Contratos protegidos

- `POST /auth/login`: conservar request, respuesta exitosa (`token`,
  `expiresIn`, `user`, `debug`) y estados/cuerpos de error documentados en
  `docs/ENDPOINTS.md`.
- Solicitudes sin `Origin`: conservar el comportamiento HTTP existente; CORS
  no debe convertirse en requisito para clientes no-browser.
- `GET /q/health`: conservar el `200` y `status: UP` sin autenticación. La
  política CORS global también se aplica a esta ruta, por decisión aprobada;
  esta decisión afecta solo a navegadores de orígenes no permitidos y no altera
  el contrato de health para clientes same-origin o no-browser.
- Mantener `GET,POST,PUT,DELETE,OPTIONS` y las cabeceras
  `accept,authorization,content-type,x-requested-with` en la política CORS.
- `AUTH_TOKEN_SECRET` sigue siendo externo en perfiles no-test, con validación
  mínima existente; no debe registrarse ni aparecer en respuestas. El literal
  de pruebas continúa restringido al perfil de test.

## Componentes afectados

- `auth/src/main/resources/application.properties`: valores CORS base y por
  perfil, y habilitación explícita de credenciales para orígenes aprobados.
- `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` y, si el
  aislamiento de perfiles lo requiere, pruebas de configuración dentro de
  `auth/src/test/java/`: caracterización, preflight y aislamiento de valores
  por perfil.
- `docs/ENDPOINTS.md` y `HALLAZGOS.md`: actualizar durante la implementación
  para reflejar credenciales habilitadas, el origen de desarrollo y el estado
  de la lista productiva, conservando el resto de secciones.

No se prevén cambios funcionales en clases Java ni dependencias nuevas.

## Decisiones técnicas y alternativas

1. **Conservar el filtro CORS global de Quarkus.** Reemplazar el patrón amplio
   con valores exactos separados por entorno; establecer de forma explícita
   `http://localhost:4200` para desarrollo y una allowlist vacía para
   producción, sin heredar el origen de desarrollo. Activar explícitamente
   `quarkus.http.cors.access-control-allow-credentials=true`. Mantener
   explícitas las listas actuales de métodos y cabeceras.

   **Alternativa considerada:** implementar una política o filtro exclusivo
   para `/auth/login`. Se descarta porque añadiría lógica y mantenimiento a
   medida para una política que ya aplica el filtro HTTP global. La opción
   global fue confirmada y restringe también CORS de `/q/health`; si el
   despliegue necesita health cross-origin desde otro origen, debe aprobarse
   ese origen antes de desplegarlo, no dejar una excepción abierta.

2. **Configurar por perfil y no codificar una lista productiva anticipada.**
   Desarrollo usa el origen aprobado; producción lee una lista explícita de
   configuración de despliegue, cuyo valor inicial es vacío. La implementación
   debe verificar con Quarkus 3.27.4 que una lista vacía se interpreta como
   denegar todos los orígenes y no como propiedad ausente ni como comodín; si
   la sustitución vacía no conserva ese significado, se deberá configurar un
   equivalente explícito que deniegue todos y probarlo antes de aceptar el
   cambio.

   **Alternativa considerada:** fijar el origen en configuración común para
   todos los perfiles. Se descarta porque podría autorizar `localhost` en
   producción. Usar expresiones regulares para aproximar una lista también se
   descarta: los valores exactos son más fáciles de revisar y probar.

3. **Mantener el secreto de firma en su mecanismo actual.** No cambiar
   `TokenService` ni mover el valor de test como parte de este cambio; comprobar
   que los perfiles no-test no adquieren un fallback y que las pruebas no
   exponen el valor.

   **Alternativa considerada:** rediseñar la carga o gestión del secreto. Se
   descarta por estar fuera del Issue y porque la configuración actual ya
   referencia `AUTH_TOKEN_SECRET`; el cambio solo preserva y verifica ese
   límite.

## Estrategia incremental

1. **Caracterizar antes del cambio de configuración:** agregar una prueba
   preflight con un origen arbitrario y registrar el comportamiento actual del
   patrón abierto; conservar como baseline las pruebas existentes de login sin
   `Origin`, errores, formato de respuesta y health. La prueba de origen
   arbitrario documenta el comportamiento que se pretende retirar.
2. **Aplicar la política por perfil:** reemplazar la expresión abierta por la
   allowlist explícita; hacer explícitos los permisos de credenciales sin
   cambiar métodos ni cabeceras. No alterar recursos ni servicios Java.
3. **Verificar el comportamiento observable:** comprobar preflight permitido
   desde `http://localhost:4200`, rechazo de origen desconocido y variantes de
   esquema/puerto, credenciales solo en el caso permitido y rechazo en el
   perfil de producción sin orígenes. Afirmar también que la configuración no
   contiene comodines y que el valor del secreto permanece externo y no se
   expone.
4. **Comprobar regresión y documentar:** ejecutar la suite de `auth`, confirmar
   que login y health conservan sus contratos, y actualizar las secciones
   pertinentes de `docs/ENDPOINTS.md` y `HALLAZGOS.md`. No modificar las
   secciones de `api` o `web`.

Las pruebas y la configuración de perfiles deben permanecer dentro de
`auth/`; no se requieren pruebas ni cambios en los otros componentes.

## Riesgos / Trade-offs

- **[Riesgo]** La política global restringe solicitudes CORS a `/q/health` y a
  cualquier otra ruta actual o futura de `auth`, no solo a login. → Mantener la
  misma allowlist global, documentar el efecto y requerir que cualquier origen
  adicional de despliegue sea aprobado explícitamente.
- **[Riesgo]** Una allowlist productiva vacía podría interpretarse de forma
  distinta a “ningún origen”, dependiendo de la resolución de configuración.
  → Validar el perfil real con una prueba de preflight de integración y no
  desplegar hasta confirmar que un origen recibe cero cabeceras CORS.
- **[Riesgo]** Activar credenciales amplía el permiso para el origen aprobado,
  aunque el contrato actual no requiere cookies. → Mantener la coincidencia
  exacta y verificar que nunca se combina con `Access-Control-Allow-Origin: *`.
- **[Trade-off]** Otros frontends locales o dominios de despliegue dejan de
  funcionar desde navegador hasta que se aprueben y configuren. → Añadir solo
  orígenes justificados, mediante configuración del entorno y sin reabrir el
  patrón general.
- **[Riesgo]** La comprobación de propiedades estáticas no basta para probar
  el preflight real ni el perfil productivo. → Combinar inspección de
  configuración y pruebas HTTP de integración con el perfil correspondiente.

## Rollback

- Si un cliente aprobado queda bloqueado por una configuración incorrecta,
  corregir la lista del entorno y redeplegar; esto evita deshacer la restricción
  global.
- Si fuera imprescindible restaurar la versión anterior, hacerlo como
  rollback de despliegue autorizado y temporal: volvería a permitir CORS desde
  cualquier origen. Registrar la excepción y su duración, aplicar mitigación
  perimetral si está disponible y reemplazarla cuanto antes por la configuración
  corregida. No revertir ni modificar por ese motivo el contrato de login o la
  configuración externa del secreto.

## Decisiones abiertas

- Ninguna para iniciar la implementación. La lista productiva permanece vacía
  hasta que se aprueben orígenes; la prueba de integración debe confirmar su
  semántica de denegación con la versión de Quarkus del proyecto.
