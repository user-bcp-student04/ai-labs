# testing_report.md

**H03 · Pagos QR para comercios — Informe y plan de pruebas**
Fecha del informe: 2026-11-06 · Rol: Ingeniero de pruebas

> **Estado global: NO EJECUTADO.** No tengo salida real de ningún comando. Este informe define pruebas y resultados *esperados*. Una persona debe ejecutar los comandos y adjuntar la salida literal. No afirmo cobertura, ni de líneas ni de criterios, sin esa evidencia. Un `skip` cuenta como **NO CUMPLIDO**.

---

## 1. Alcance y qué cubre cada herramienta

| Capa | Herramienta | Qué verifica |
|---|---|---|
| API FastAPI (`api/app/`) | `pytest` + `fastapi.testclient.TestClient` (`httpx`) | Base mínima del Backend: `/health`, formato de error `{"code","message"}`, ausencia de endpoints y persistencia H03 en servidor, y pines de dependencias. |
| Mock W2/W3 (solo lectura) | `pytest` + `httpx.Client` contra el mock configurado | El contrato **supuesto** (S-4, S-5) frente al mock real. |
| Frontend Angular 17 | Angular specs (Jasmine/Karma, ver T-4) con `HttpTestingController` | Los criterios CA-1 a CA-6, que viven en el navegador. |
| Recorrido completo | E2E manual guiado, con el mock configurado | CA-1 a CA-7 de extremo a extremo y limitaciones. |

La capa FastAPI no implementa W2 ni W3 (S-1). Por eso los criterios de H03 se prueban en el frontend, contra el mock y en E2E. Las pruebas pytest del API comprueban que esa decisión se mantiene: no hay endpoints de negocio ni escritura en disco.

## 2. Supuestos declarados

| ID | Supuesto | Consecuencia si es falso |
|---|---|---|
| T-1 | El contrato W2/W3 es el de trabajo del Arquitecto (§3: `payload`, `qrId`, `Idempotency-Key`, códigos `QR_*`, `AMOUNT_INVALID`, `IDEMPOTENCY_CONFLICT`). P-1 sigue abierto. | Los `MOCK-*` fallarán. Eso es un hallazgo sobre el contrato, no un fallo atribuible al cambio. Se corrige la prueba contra `design.md`/`spec.md`. |
| T-2 | Rutas de estado y recibo: `GET /payments/{id}` y `GET /payments/{id}/receipt` (supuestas por el Frontend). | Igual que T-1. |
| T-3 | Los archivos de `backend_spec.md` (`api/app/*`) existen en el árbol bajo prueba y `app` es importable con `api/` como directorio de trabajo o `PYTHONPATH`. | Si el repo ya tenía `api/app/` distinto, los `API-*`/`ERR-*` que no apliquen se **corrigen o descartan** (regla de línea base). |
| T-4 | El frontend usa el runner por defecto de Angular 17: Karma + Jasmine, con Chrome headless. Si el repo usa otro runner (P-2), hay que portar la sintaxis `describe/it/expect`, que es casi idéntica en Jest. | Las specs no compilan ni corren hasta portarlas. |
| T-5 | `pytest` y `httpx` están instalados en el entorno de pruebas del repo. `api/requirements.txt` del Backend no los lista. No fijo versiones porque no las conozco y no inventaré pines. | Instalarlos según el requirements de desarrollo del repo. |
| T-6 | No recibí entrega de Seguridad. No puedo mapear correcciones concretas de Seguridad. Verifico las propiedades de seguridad que sí declara `backend_spec.md` y el frontend (§5 de este informe). | Cuando llegue la entrega, añadir filas a §5. |
| T-7 | Los payloads, `qrId` y escenarios del mock no son conocidos. Los define el mock configurado y se pasan por variables de entorno obligatorias (§7). Si falta una, la prueba **falla**, no se omite. | n/a |
| T-8 | La decodificación real de QR depende de `BarcodeDetector` o de una librería aprobada (P-3). Las specs usan un motor falso inyectado vía `QR_IMAGE_ENGINE`. | La lectura de un QR real solo se verifica en E2E-01. |
| T-9 | Los comandos del frontend (`npm ci`, `npm run build`, `npx ng test --watch=false --browsers=ChromeHeadless`) son supuestos de un proyecto Angular estándar (P-2). El único comando oficial confirmado por el laboratorio es `python tools/lab.py test api`. | Sustituir por los scripts reales del `package.json` y anotarlo en el registro. |

## 3. Orden de ejecución

Regla: primero la línea base y después el cambio. Una prueba que falla en la línea base se **corrige o se descarta**; no se atribuye al cambio.

| Fase | Contenido | Pruebas |
|---|---|---|
| **0. Preparación** | Entorno, dependencias, `pip check`, variables del mock. | §8.1 |
| **A. Línea base** | Toda la suite existente más las pruebas nuevas que no dependen del código nuevo del frontend, sobre el árbol **antes** de aplicar los componentes Angular de H03. | `python tools/lab.py test api`; `API-*`, `ERR-*`, `PER-*`, `DEP-*`; `MOCK-*` (el mock es de solo lectura, igual antes y después); suite de frontend existente sin las specs `FE-*` de H03. |
| **B. Cambio** | Specs Angular de H03 sobre el árbol con los componentes nuevos, y compilación. | `FE-DEC`, `FE-SVC`, `FE-ERR`, `FE-STO`, `FE-PAGO`, `FE-HIST`; build. |
| **C. Integración y CA-7** | Verificación del repositorio, E2E con el mock y registro de limitaciones. | `E2E-01`…`E2E-09`. |

Una fase A en rojo bloquea la B hasta clasificar cada fallo como defecto de la prueba (se corrige), del entorno (se corrige el entorno) o preexistente (se registra).

## 4. Trazabilidad: criterio → prueba → resultado esperado → estado

| Criterio | Pruebas | Resultado esperado | Estado |
|---|---|---|---|
| **CA-1** Decodificar en el navegador y enviar solo el payload a W3 `POST /qrs/resolve` | `FE-DEC-01…06`, `FE-SVC-01`, `FE-PAGO-01`, `MOCK-01…02`, `E2E-01` | El decodificador devuelve solo texto (motor inyectado). El cuerpo de `POST /qrs/resolve` es exactamente `{"payload":"…"}`, sin Blob/FormData/campos de imagen. Un archivo no imagen o sin QR no genera ninguna petición. El mock acepta ese cuerpo. | NO EJECUTADO |
| **CA-2** Mostrar comercio e importe antes de confirmar; importe positivo en monto abierto | `FE-PAGO-02…06`, `E2E-02`, `E2E-03` | Tras resolver, la vista muestra comercio e importe y **no** hay `POST /payments`. En monto abierto, el botón está deshabilitado con vacío, `0`, `-5`, `NaN` e `Infinity`, y habilitado con `10`. Los mensajes son los de §5 del frontend. `confirm()` sin importe válido no envía nada. | NO EJECUTADO |
| **CA-3** Crear pagos con W2 `POST /payments`, preservando `qrId` e idempotencia | `FE-SVC-06…07`, `FE-PAGO-07…10`, `MOCK-08…11`, `E2E-04` | El cuerpo es `{qrId, amount, currency}` con el `qrId` recibido de W3 y la cabecera `Idempotency-Key`. Doble confirmación → 1 petición. Reintento tras error de red: misma clave. Importe distinto o `IDEMPOTENCY_CONFLICT`: clave nueva. El mock repite el mismo `paymentId` con la misma clave y responde 409 con cuerpo distinto. | NO EJECUTADO |
| **CA-4** Consultar estado y recibos en W2; eventos manuales, no webhooks | `FE-SVC-08…09`, `FE-PAGO-11…12`, `FE-PAGO-19`, `FE-HIST-07…09`, `MOCK-12…13`, `MOCK-15`, `E2E-05` | «Actualizar estado» y «Ver recibo» hacen `GET` a W2 solo por acción del usuario y reflejan el resultado. No hay peticiones espontáneas. El texto no habla de webhooks ni de notificación automática. En el mock, el estado no cambia sin acción. | NO EJECUTADO |
| **CA-5** Historial local, filtrable, solo pagos de este flujo, con «Fecha local registrada» | `FE-STO-01…09`, `FE-PAGO-11`, `FE-PAGO-17`, `FE-HIST-01…06`, `E2E-06`, `E2E-07` | Solo `confirm()` exitoso escribe en `merchantQrPayments.history` (`schemaVersion: 1`). Sin duplicados por `paymentId`. Los filtros no hacen red. La columna se llama «Fecha local registrada» y el `datetime` es el ISO guardado. Entradas corruptas se ignoran. Un formato ajeno no se sobrescribe y se avisa. El evento `storage` refresca la lista. | NO EJECUTADO |
| **CA-6** Recuperación ante QR inválido, desconocido, expirado o conflicto | `FE-ERR-01…09`, `FE-SVC-03…05`, `FE-PAGO-13…16`, `FE-PAGO-18`, `MOCK-03…06`, `MOCK-14`, `E2E-08` | Cada código muestra el título y la acción de §6 del frontend. `QR_EXPIRED` y `QR_CONFLICT` descartan la revisión. Con `QR_CONFLICT`, «Volver a validar el QR» reenvía el mismo payload a W3. Ningún error deja un pago en el historial. Un mensaje de servicio con HTML se muestra como texto. | NO EJECUTADO |
| **CA-7** Compilación, verificación del repo y E2E con el mock; resultados reales y limitaciones | Fases A, B y C completas; `API-*`, `ERR-*`, `PER-*`, `DEP-*`; `E2E-01…09`; §10 | Build sin errores. `python tools/lab.py test api` verde, 0 skips. Specs verdes, 0 skips. E2E ejecutados con el mock. El registro §9 contiene salida literal y la lista de limitaciones. Si algo falla o se omite, el criterio **no** se da por cumplido. | NO EJECUTADO |

## 5. Contratos y seguridad

### 5.1 Contrato de API y persistencia

| Contrato | Prueba | Esperado |
|---|---|---|
| `GET /health` → 200 `{"status":"ok","service":<SERVICE_NAME>}` | `API-01…03` | Igual. |
| Errores `{"code","message"}` con códigos de `backend_spec.md` §5 | `ERR-01…06`, `API-04…06` | 404 `NOT_FOUND`, 405 `METHOD_NOT_ALLOWED`, 422 `VALIDATION_ERROR`, 500 `INTERNAL_ERROR`, 409/413/401/403/400 con sus códigos. |
| La API no implementa W2/W3 ni escribe en disco (S-1, §6–7 del backend) | `API-06`, `API-07`, `PER-01`, `PER-02` | Solo existe `/health`. El directorio de trabajo y el de subidas aislados quedan intactos. |
| Contrato W3 y W2 supuesto | `MOCK-01…15` | Ver T-1 y T-2. |
| Persistencia local `merchantQrPayments.history` con `schemaVersion: 1` | `FE-STO-*`, `FE-PAGO-11/17` | Ver CA-5. |

### 5.2 Propiedades de seguridad comprobadas (T-6: no hay entrega de Seguridad)

| Propiedad | Prueba | Esperado |
|---|---|---|
| El 422 no devuelve valores enviados, solo nombres de campo | `ERR-03`, `ERR-04`, `ERR-05` | El valor sentinela no aparece en la respuesta. |
| El 500 es genérico, sin traza ni mensaje de la excepción; la traza va al log | `ERR-06` | Cuerpo fijo. Un registro `ERROR` en el logger `app.errors`. |
| Los `detail` de errores 5xx y los de códigos con mensaje fijo no se filtran | `ERR-01` | El mensaje es el fijo del mapa. |
| La API no recibe subidas ni escribe en disco | `PER-01`, `PER-02` | Sin archivos nuevos. Sin `requestBody` en OpenAPI. |
| La imagen no sale del navegador | `FE-PAGO-01`, `FE-SVC-01`, `E2E-01` | Solo `{"payload"}`. |
| El mensaje del servicio se muestra como texto plano | `FE-PAGO-18` | No se crea ningún elemento HTML a partir del mensaje. |
| Pines de dependencias exactos e instalados | `DEP-01`, `DEP-02` | Todos `==` y coinciden con lo instalado. |
| Vulnerabilidades de los pines (OSV) | **Procedimiento manual obligatorio en §8.5** | No hay verificación opcional ni `skip`. Las versiones de `requirements.txt` **no están verificadas** contra PyPI/OSV a 2026-11-06. Ningún CA depende de esto. Se registra como hallazgo aparte. |

## 6. Catálogo de casos por tipo

| Tipo | Casos |
|---|---|
| **Positivo** | `API-01`, `API-02`, `ERR-01`, `FE-DEC-01`, `FE-SVC-01/02/06/08`, `FE-PAGO-02/07/11/12`, `FE-STO-01`, `FE-HIST-01…03/07/08`, `MOCK-01/02/08/09/12`, `E2E-01…07` |
| **Negativo** | `API-04…06`, `ERR-02…06`, `FE-DEC-02…06`, `FE-SVC-03…05/07/09`, `FE-ERR-*`, `FE-PAGO-03…06/10/13…16/18`, `FE-STO-03…05/08`, `FE-HIST-09`, `MOCK-03…07/10/11/13/14`, `E2E-08` |
| **Borde** | `API-03`, `API-08/09`, `ERR-05`, `FE-DEC-05/06`, `FE-SVC-08/10`, `FE-PAGO-03/06/08/09`, `FE-STO-02/06/07`, `FE-HIST-05/06`, `MOCK-07/11/15`, `E2E-07` |
| **Integración** | `API-10`, `PER-01`, `FE-PAGO-*` (componente + servicios + historial + HTTP simulado), `FE-HIST-07/08`, `MOCK-01…15` (httpx contra el mock real), `E2E-01…09` |

Detalle de las pruebas del frontend:

- **FE-DEC (decodificador):**
  - 01: devuelve el texto.
  - 02: no imagen.
  - 03: motor no disponible.
  - 04: sin QR.
  - 05: motor que falla.
  - 06: bytes ilegibles.
- **FE-SVC (servicio HTTP):**
  - 01: cuerpo solo con payload.
  - 02: parseo fijo y abierto.
  - 03: respuesta fuera de contrato.
  - 04: mapeo de error 410.
  - 05: red caída.
  - 06: cabecera y `qrId`.
  - 07: respuesta de pago inválida.
  - 08: codificación de URL de estado.
  - 09: recibo no objeto.
  - 10: claves únicas.
- **FE-ERR (guías):**
  - 01: tabla por código.
  - 02: conflicto con revalidar.
  - 03: 413 por estado.
  - 04: 401/403.
  - 05: 404 según contexto.
  - 06: sin conexión.
  - 07: 5xx.
  - 08: mensaje del servicio.
  - 09: razones de decodificación.
- **FE-STO (historial local):**
  - 01: esquema.
  - 02: deduplicación.
  - 03: entradas corruptas.
  - 04: JSON ilegible.
  - 05: esquema ajeno.
  - 06: evento `storage`.
  - 07: clave ajena.
  - 08: cuota o almacenamiento caído.
  - 09: actualizar estado.
- **FE-PAGO (recorrido):**
  - 01: solo payload.
  - 02: revisión antes de confirmar.
  - 03: importe abierto, tabla de habilitación.
  - 04: mensajes de importe.
  - 05: confirmación bloqueada.
  - 06: QR fijo con importe inválido.
  - 07: cuerpo y cabecera.
  - 08: doble confirmación.
  - 09: clave reutilizada o nueva.
  - 10: `IDEMPOTENCY_CONFLICT`.
  - 11: éxito, historial y sin peticiones extra.
  - 12: refrescar manual.
  - 13: errores de resolve.
  - 14: expirado en pago.
  - 15: conflicto en pago.
  - 16: respuesta inválida.
  - 17: aviso de historial.
  - 18: texto plano.
  - 19: sin lenguaje de webhooks.
- **FE-HIST (historial):**
  - 01: vacío.
  - 02: etiqueta y fecha.
  - 03: filtro de texto.
  - 04: filtro de estado sin red.
  - 05: sin coincidencias y limpiar.
  - 06: entradas corruptas.
  - 07: refrescar y guardia de ocupado.
  - 08: recibo.
  - 09: error de recibo.

## 7. Datos de prueba

| Dato | Origen | Uso |
|---|---|---|
| `H03_W3_BASE_URL`, `H03_W2_BASE_URL` | URLs del mock configurado | `MOCK-*` |
| `H03_QR_PAYLOAD_FIXED`, `H03_QR_PAYLOAD_OPEN` | Payloads de QR válidos de importe fijo y de monto abierto, definidos por el mock | `MOCK-01/02/08…15` |
| `H03_QR_PAYLOAD_INVALID`, `…_UNKNOWN`, `…_EXPIRED`, `…_CONFLICT` | Payloads que el mock resuelve con cada error | `MOCK-03…06` |
| `H03_QR_ID_EXPIRED`, `H03_QR_ID_CONFLICT` | `qrId` que el mock rechaza en `POST /payments` | `MOCK-14` |
| Sentinelas `987654`, `clave-secreta-123`, `password=abc` | Embebidos en las pruebas | `ERR-*` |
| Entradas de historial sintéticas (`pay_1`…`pay_3`) | Embebidas en las specs | `FE-HIST-*`, `FE-STO-*` |
| Imagen de prueba (PNG 8×8 generada con `canvas`) | Generada en la spec | `FE-DEC-*` |
| Imagen QR real y un archivo no imagen | A cargo de quien ejecute E2E; usa un QR que el mock resuelva | `E2E-01…08` |

Hasta que la persona rellene las variables `H03_*` con datos del mock, **no conozco esos valores**. Sin ellas los `MOCK-*` **fallan** (no se omiten).

## 8. Preparación y comandos (todo **NO EJECUTADO**)

Conserva cada salida completa en `evidencia/` (`tee`).

### 8.1 Fase 0: preparación

```bash
mkdir -p evidencia
git rev-parse HEAD | tee evidencia/00_commit.txt
git status --short | tee evidencia/00_status.txt
python --version | tee evidencia/00_python.txt

cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip check            | tee ../evidencia/00_pip_check.txt
pip freeze | grep -iE '^(fastapi|starlette|pydantic|uvicorn|pytest|httpx)==' | tee ../evidencia/00_pip_freeze.txt
python -m pytest --version
python -c "import httpx; print(httpx.__version__)"
cd ..

# Mock configurado (valores del mock real, ver §7):
export H03_W3_BASE_URL="..." H03_W2_BASE_URL="..."
export H03_QR_PAYLOAD_FIXED="..." H03_QR_PAYLOAD_OPEN="..."
export H03_QR_PAYLOAD_INVALID="..." H03_QR_PAYLOAD_UNKNOWN="..."
export H03_QR_PAYLOAD_EXPIRED="..." H03_QR_PAYLOAD_CONFLICT="..."
export H03_QR_ID_EXPIRED="..." H03_QR_ID_CONFLICT="..."
```

### 8.2 Fase A: línea base

```bash
# A1. Suite oficial del repo (incluye las pruebas nuevas de api/tests/)
python tools/lab.py test api 2>&1 | tee evidencia/A1_lab_test_api.txt

# A2. Pruebas H03 del API y del mock (nombres de archivo exactos), -rs lista skips
cd api
python -m pytest tests/test_h03_health_contract.py tests/test_h03_error_format.py \
  tests/test_h03_no_server_persistence.py tests/test_h03_dependency_pins.py \
  tests/test_h03_mock_contract.py -v -rs 2>&1 | tee ../evidencia/A2_pytest_h03.txt
cd ..

# A3. Criterio de skips: debe imprimir 0
grep -ci "skipped" evidencia/A1_lab_test_api.txt evidencia/A2_pytest_h03.txt

# A4. Suite de frontend existente (antes de añadir las specs FE-*), comando según T-9
npx ng test --watch=false --browsers=ChromeHeadless 2>&1 | tee evidencia/A4_ng_test_baseline.txt
```

### 8.3 Fase B: cambio

```bash
npm ci 2>&1 | tee evidencia/B1_npm_ci.txt
npx ng test --watch=false --browsers=ChromeHeadless 2>&1 | tee evidencia/B2_ng_test_h03.txt
npm run build 2>&1 | tee evidencia/B3_build.txt
```

### 8.4 Fase C: repositorio y E2E

```bash
npm run                                  # lista los scripts reales (P-2); anota cuál es la verificación del repo
npm run <script-de-verificacion> 2>&1 | tee evidencia/C1_verificacion_repo.txt
# E2E manual: seguir §8.6 y completar la tabla de §9 con capturas del panel de red.
```

### 8.5 Procedimiento manual obligatorio: vulnerabilidades de los pines (no es opcional ni `skip`)

Para cada pin de `api/requirements.txt` (`fastapi`, `starlette`, `pydantic`, `uvicorn`):

```bash
curl -s https://api.osv.dev/v1/query \
  -d '{"package":{"name":"starlette","ecosystem":"PyPI"},"version":"0.41.3"}' \
  | tee evidencia/C2_osv_starlette.json
```

Anota la fecha, la fuente y el resultado de cada consulta, y verifica en PyPI que cada versión existe. Cualquier hallazgo se registra como hallazgo de Seguridad/Arquitectura. No modifica el veredicto de CA-1…CA-7, porque el Issue no es una actualización de dependencias. No he ejecutado ninguna consulta.

### 8.6 E2E manuales (con el mock configurado)

Requisito: navegador con `BarcodeDetector` (ver limitación L-1). Abre el panel de red y guarda capturas.

| ID | Pasos | Esperado |
|---|---|---|
| E2E-01 | En `/pagar-qr`, cargar una imagen con un QR válido. | `POST /qrs/resolve` con cuerpo `{"payload":"…"}` y sin datos de imagen. Aparece «Validando el QR…». |
| E2E-02 | Con QR de importe fijo, observar la revisión. | Comercio e importe visibles. **Sin** `POST /payments` aún. |
| E2E-03 | Con QR de monto abierto, probar vacío, `0`, `-5` y `10`. | Botón deshabilitado con los tres primeros y mensajes correctos. Habilitado con `10`. El `amount` enviado es `10`. |
| E2E-04 | Pulsar «Confirmar pago» dos veces seguidas. | Un solo `POST /payments` con `qrId` e `Idempotency-Key`. Se muestran referencia, ID y estado. |
| E2E-05 | Esperar 30 s sin actuar. Luego pulsar «Actualizar estado» y, en `/historial`, «Ver recibo». | Durante la espera no hay peticiones nuevas ni cambios de estado. Después se ven los `GET` a W2 y el recibo campo a campo. |
| E2E-06 | En `/historial`: comprobar la etiqueta, filtrar por texto y estado, y abrir dos pestañas creando un pago en una. | Columna «Fecha local registrada». Los filtros no emiten peticiones. La otra pestaña se actualiza sin duplicados. |
| E2E-07 | Escribir basura en `merchantQrPayments.history` (DevTools) y recargar. Luego pagar. | La pantalla no se rompe. Tras pagar sale el aviso de que no se guardó en el historial. La basura no se sobrescribe. |
| E2E-08 | Con el mock configurado para `QR_INVALID`, `QR_UNKNOWN`, `QR_EXPIRED`, `QR_CONFLICT` (en resolve y en payments), 413, 401, 5xx y mock apagado. | Guía de §6 del frontend en cada caso. Ningún pago a medias en el historial. Con el mock apagado, el reintento de pago reutiliza la clave. |
| E2E-09 | Cargar un archivo que no es imagen y una imagen sin QR. | Mensajes de lectura local. No hay ninguna petición a W3. |

## 9. Registro de resultados (a completar con salida real)

| Prueba / comando | Fecha y hora | Resultado | Archivo de evidencia | Observaciones |
|---|---|---|---|---|
| A1 `python tools/lab.py test api` | | NO EJECUTADO | `evidencia/A1_…` | |
| A2 pytest H03 | | NO EJECUTADO | `evidencia/A2_…` | |
| A3 conteo de skips | | NO EJECUTADO | | Debe ser 0 |
| A4 suite frontend previa | | NO EJECUTADO | `evidencia/A4_…` | |
| B2 specs `FE-*` | | NO EJECUTADO | `evidencia/B2_…` | |
| B3 build | | NO EJECUTADO | `evidencia/B3_…` | |
| C1 verificación del repo | | NO EJECUTADO | `evidencia/C1_…` | |
| C2 OSV de pines | | NO EJECUTADO | `evidencia/C2_…` | |
| E2E-01 … E2E-09 | | NO EJECUTADO | capturas | |

## 10. Limitaciones y brechas conocidas

- **L-1:** `BarcodeDetector` no existe en todos los navegadores (Firefox, Safari de escritorio, Chrome Windows/Linux, entre otros). Sin una librería aprobada (P-3), E2E-01…08 solo corren en un navegador compatible. En ese caso, E2E en CI headless **no se puede cumplir** hasta resolver P-3. Eso es una limitación a registrar, no un resultado.
- **L-2:** El contrato W2/W3 (P-1) es supuesto. Los `MOCK-*` y las rutas de estado y recibo pueden fallar por ese motivo.
- **L-3:** Los datos del mock (T-7) son desconocidos para mí. Sin esas variables, los `MOCK-*` fallan.
- **L-4:** No hay prueba automática de polling en el tiempo. Se cubre con `E2E-05` (espera de 30 s) y revisando que el código no usa temporizadores.
- **L-5:** No se mide cobertura. No afirmo ningún porcentaje.
- **L-6:** P-4 (unidad del importe), P-5 (clave de historial preexistente), P-6 (límite de payload), P-7 (rol de comercio) y P-8 (credenciales) siguen abiertos. No hay pruebas de límites de payload ni de formato de moneda por eso.
- **L-7:** No se puede atribuir ni afirmar que el estado del mock «cambie por sí solo» o no. `MOCK-15` solo observa 3 s.
- **L-8:** No hay pruebas de rendimiento ni de carga.

## 11. Limpieza

- **pytest:** `tmp_path` y `monkeypatch` se limpian solos. Ejecuta `rm -rf api/.pytest_cache`.
- **Entorno:** `deactivate` y, si procede, `rm -rf api/.venv`.
- **Variables:** `unset` de las `H03_*`.
- **Mock:** los `MOCK-08…15` crean pagos. Reinicia o restablece el mock con **su** procedimiento. No modifiques su código (es de solo lectura).
- **Navegador:** en cada pestaña de E2E, `localStorage.removeItem('merchantQrPayments.history')`. Las specs lo hacen solas (`beforeEach`/`afterEach`).
- **Evidencias:** archiva `evidencia/` con el hash del commit.

## 12. Archivos de prueba entregados

Todos son archivos nuevos. No se modifica ninguna aserción existente.

- `api/tests/test_h03_health_contract.py`
- `api/tests/test_h03_error_format.py`
- `api/tests/test_h03_no_server_persistence.py`
- `api/tests/test_h03_dependency_pins.py`
- `api/tests/test_h03_mock_contract.py`
- `src/app/qr-pagos/qr-decoder.service.spec.ts`
- `src/app/qr-pagos/qr-api.service.spec.ts`
- `src/app/qr-pagos/error-messages.spec.ts`
- `src/app/qr-pagos/payment-history.service.spec.ts`
- `src/app/qr-pagos/qr-pago.component.spec.ts`
- `src/app/qr-pagos/historial.component.spec.ts`

---

# Pruebas pytest (API y mock)

```python
# api/tests/test_h03_health_contract.py
"""H03 · API-01…API-10: contrato de /health, rutas inexistentes y configuración.

Supuesto T-3: `app` es importable (se ejecuta con api/ como directorio de trabajo).
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config
from app.main import app

API_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_api_01_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json() == {"status": "ok", "service": config.SERVICE_NAME}


def test_api_02_health_usa_el_nombre_de_servicio_configurado(client, monkeypatch):
    monkeypatch.setattr(config, "SERVICE_NAME", "svc-h03-prueba")
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "svc-h03-prueba"}


def test_api_03_health_ignora_parametros_de_consulta(client):
    resp = client.get("/health", params={"x": "1", "payload": "abc"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": config.SERVICE_NAME}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_api_04_health_rechaza_otros_metodos(client, method):
    resp = getattr(client, method)("/health")
    assert resp.status_code == 405
    assert resp.json() == {"code": "METHOD_NOT_ALLOWED", "message": "Método no permitido."}
    assert "GET" in resp.headers.get("allow", "")


def test_api_05_ruta_inexistente_devuelve_404_con_formato_unico(client):
    resp = client.get("/no-existe")
    assert resp.status_code == 404
    assert resp.json() == {"code": "NOT_FOUND", "message": "Recurso no encontrado."}


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/qrs/resolve"),
        ("post", "/payments"),
        ("get", "/payments/pay_1"),
        ("get", "/payments/pay_1/receipt"),
    ],
)
def test_api_06_los_endpoints_w2_w3_no_viven_en_esta_api(client, method, path):
    """S-1: W2/W3 son servicios externos; FastAPI no los implementa ni los proxifica."""
    resp = getattr(client, method)(path)
    assert resp.status_code == 404
    assert resp.json() == {"code": "NOT_FOUND", "message": "Recurso no encontrado."}


def test_api_07_openapi_expone_solo_health(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert set(resp.json()["paths"]) == {"/health"}


def _read_config(extra_env: dict, drop: tuple) -> list:
    env = {k: v for k, v in os.environ.items() if k not in drop}
    env.update(extra_env)
    env["PYTHONPATH"] = str(API_DIR)
    code = (
        "import json; from app import config; "
        "print(json.dumps([config.SERVICE_NAME, config.API_VERSION, config.LOG_LEVEL]))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=API_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_api_08_configuracion_por_defecto():
    values = _read_config({}, drop=("SERVICE_NAME", "API_VERSION", "LOG_LEVEL"))
    assert values == ["merchant-qr-api", "0.1.0", "INFO"]


def test_api_09_configuracion_desde_variables_de_entorno():
    values = _read_config(
        {"SERVICE_NAME": "otro-servicio", "API_VERSION": "9.9.9", "LOG_LEVEL": "debug"},
        drop=(),
    )
    assert values == ["otro-servicio", "9.9.9", "DEBUG"]


def _one_health_call(_: int) -> tuple:
    with TestClient(app) as c:
        resp = c.get("/health")
        return resp.status_code, resp.json()


def test_api_10_health_concurrente_sin_estado_compartido():
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(_one_health_call, range(20)))
    assert len(results) == 20
    assert all(status == 200 for status, _ in results)
    assert all(body == {"status": "ok", "service": config.SERVICE_NAME} for _, body in results)
```

```python
# api/tests/test_h03_error_format.py
"""H03 · ERR-01…ERR-06: formato único de error y no filtración de datos.

Se usa una app local con los handlers reales de app.errors, sin modificar la app principal.
"""
import logging

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.errors import register_error_handlers


class _Body(BaseModel):
    amount: int = Field(gt=0)


def _build_app() -> FastAPI:
    local = FastAPI()
    register_error_handlers(local)

    @local.get("/n")
    def n(n: int):
        return {"n": n}

    @local.post("/pay")
    def pay(body: _Body):
        return {"ok": True}

    @local.get("/boom")
    def boom():
        raise RuntimeError("clave-secreta-123")

    @local.get("/http/{status}")
    def http_error(status: int, detail: str):
        raise HTTPException(status_code=status, detail=detail)

    @local.get("/auth")
    def auth():
        raise HTTPException(status_code=401, detail="x", headers={"WWW-Authenticate": "Bearer"})

    return local


@pytest.fixture()
def client():
    return TestClient(_build_app(), raise_server_exceptions=False)


@pytest.mark.parametrize(
    "status,detail,code,message",
    [
        (400, "secreto-400", "INVALID_INPUT", "Entrada inválida."),
        (401, "secreto-401", "UNAUTHORIZED", "Autenticación requerida."),
        (403, "secreto-403", "FORBIDDEN", "No tienes permisos para esta operación."),
        (409, "secreto-409", "CONFLICT", "Conflicto con el estado actual del recurso."),
        (413, "secreto-413", "PAYLOAD_TOO_LARGE", "El contenido enviado supera el tamaño permitido."),
        (418, "soy-tetera", "HTTP_ERROR", "soy-tetera"),
        (503, "password=abc", "INTERNAL_ERROR", "Error interno del servidor."),
    ],
)
def test_err_01_httpexception_usa_formato_unico_y_mensajes_fijos(client, status, detail, code, message):
    resp = client.get(f"/http/{status}", params={"detail": detail})
    assert resp.status_code == status
    assert resp.json() == {"code": code, "message": message}
    assert set(resp.json()) == {"code", "message"}


def test_err_02_se_conservan_las_cabeceras_de_la_excepcion(client):
    resp = client.get("/auth")
    assert resp.status_code == 401
    assert resp.headers["www-authenticate"] == "Bearer"
    assert resp.json()["code"] == "UNAUTHORIZED"


def test_err_03_422_en_query_lista_solo_nombres_de_campo(client):
    resp = client.get("/n", params={"n": "valor-sentinela-987654"})
    assert resp.status_code == 422
    assert resp.json() == {"code": "VALIDATION_ERROR", "message": "Entrada inválida en: query.n."}
    assert "valor-sentinela-987654" not in resp.text


def test_err_04_422_en_cuerpo_no_devuelve_los_valores_enviados(client):
    resp = client.post("/pay", json={"amount": -987654})
    assert resp.status_code == 422
    assert resp.json() == {"code": "VALIDATION_ERROR", "message": "Entrada inválida en: body.amount."}
    assert "987654" not in resp.text

    missing = client.post("/pay", json={})
    assert missing.status_code == 422
    assert missing.json()["message"] == "Entrada inválida en: body.amount."


def test_err_05_422_con_json_ilegible_no_refleja_el_cuerpo(client):
    resp = client.post("/pay", content="no-json-secret", headers={"content-type": "application/json"})
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"
    assert "no-json-secret" not in resp.text


def test_err_06_500_es_generico_y_la_traza_solo_va_al_log(client, caplog):
    with caplog.at_level(logging.ERROR, logger="app.errors"):
        resp = client.get("/boom")
    assert resp.status_code == 500
    assert resp.json() == {"code": "INTERNAL_ERROR", "message": "Error interno del servidor."}
    assert "clave-secreta-123" not in resp.text
    assert "Traceback" not in resp.text
    assert any(r.name == "app.errors" and r.levelno == logging.ERROR and r.exc_info for r in caplog.records)
```

```python
# api/tests/test_h03_no_server_persistence.py
"""H03 · PER-01, PER-02: la API no escribe en disco ni acepta subidas (S-1, backend §6-7).

Aísla el directorio de trabajo y las variables de subida con tmp_path y monkeypatch.
Supuesto: la app no usa UPLOAD_DIR; se fija para detectar cualquier escritura inesperada.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def aislado(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    workdir = tmp_path / "cwd"
    uploads.mkdir()
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    for var in ("UPLOAD_DIR", "UPLOADS_DIR", "DATA_DIR"):
        monkeypatch.setenv(var, str(uploads))
    return tmp_path


def _snapshot(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*"))


def test_per_01_las_peticiones_no_escriben_en_disco(aislado):
    before = _snapshot(aislado)
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/no-existe").status_code == 404
        files = {"file": ("qr.png", b"\x89PNG" + b"0" * 1024, "image/png")}
        assert client.post("/health", files=files).status_code == 405
        assert client.post("/payments", json={"qrId": "qr_1", "amount": 10, "currency": "COP"}).status_code == 404
        assert client.post("/qrs/resolve", content=b"x" * (1024 * 1024)).status_code == 404
    assert _snapshot(aislado) == before
    assert list((aislado / "uploads").iterdir()) == []
    assert list((aislado / "cwd").iterdir()) == []


def test_per_02_openapi_no_declara_cuerpos_ni_subidas():
    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]
    for path, operations in paths.items():
        for method, operation in operations.items():
            assert "requestBody" not in operation, f"{method.upper()} {path} acepta cuerpo"
```

```python
# api/tests/test_h03_dependency_pins.py
"""H03 · DEP-01, DEP-02: pines exactos de api/requirements.txt y coincidencia con lo instalado.

No consulta PyPI/OSV (requiere red): ver el procedimiento manual obligatorio del informe, §8.5.
"""
from importlib.metadata import version
from pathlib import Path

import pytest

REQUIREMENTS = Path(__file__).resolve().parents[1] / "requirements.txt"


def _lines():
    out = []
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def test_dep_01_todas_las_dependencias_estan_fijadas_con_igualdad_exacta():
    lines = _lines()
    assert lines, "requirements.txt no contiene dependencias"
    for line in lines:
        assert "==" in line, f"Dependencia sin pin exacto: {line}"
        assert not any(op in line for op in (">=", "<=", "~=", ">", "<", "*")), line


@pytest.mark.parametrize("line", _lines())
def test_dep_02_la_version_instalada_coincide_con_el_pin(line):
    name, pinned = [part.strip() for part in line.split("==", 1)]
    assert version(name) == pinned
```

```python
# api/tests/test_h03_mock_contract.py
"""H03 · MOCK-01…MOCK-15: contrato W3/W2 contra el mock configurado (solo lectura).

Supuestos T-1/T-2/T-7: el contrato es el de trabajo del Arquitecto y los datos
vienen de variables de entorno H03_*. Si falta una variable, la prueba FALLA (no se omite).
Un fallo por contrato distinto es un hallazgo sobre P-1, no un defecto atribuible al cambio.
"""
import os
import time
import uuid

import httpx
import pytest

IDEM = "Idempotency-Key"


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        pytest.fail(f"Falta la variable obligatoria {name} (datos del mock configurado).", pytrace=False)
    return value


@pytest.fixture()
def w3():
    with httpx.Client(base_url=_env("H03_W3_BASE_URL"), timeout=10) as c:
        yield c


@pytest.fixture()
def w2():
    with httpx.Client(base_url=_env("H03_W2_BASE_URL"), timeout=10) as c:
        yield c


def _resolve(w3, payload: str) -> httpx.Response:
    return w3.post("/qrs/resolve", json={"payload": payload})


def _pay(w2, qr_id: str, amount, currency: str, key: str) -> httpx.Response:
    return w2.post(
        "/payments",
        json={"qrId": qr_id, "amount": amount, "currency": currency},
        headers={IDEM: key},
    )


def _resolved(w3, env_name: str) -> dict:
    resp = _resolve(w3, _env(env_name))
    assert resp.status_code == 200, resp.text
    return resp.json()


def _created(w2, qr: dict, amount) -> dict:
    resp = _pay(w2, qr["qrId"], amount, qr["currency"], str(uuid.uuid4()))
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def test_mock_01_resolve_qr_de_importe_fijo(w3):
    body = _resolved(w3, "H03_QR_PAYLOAD_FIXED")
    assert isinstance(body["qrId"], str) and body["qrId"]
    assert isinstance(body["merchant"]["name"], str) and body["merchant"]["name"]
    assert body["amountType"] == "fixed"
    assert isinstance(body["amount"], (int, float)) and body["amount"] > 0
    assert isinstance(body["currency"], str) and body["currency"]


def test_mock_02_resolve_qr_de_monto_abierto(w3):
    body = _resolved(w3, "H03_QR_PAYLOAD_OPEN")
    assert body["amountType"] == "open"
    assert body.get("amount") in (None,)
    assert body["qrId"] and body["merchant"]["name"] and body["currency"]


@pytest.mark.parametrize(
    "env_name,status,code",
    [
        ("H03_QR_PAYLOAD_INVALID", 400, "QR_INVALID"),
        ("H03_QR_PAYLOAD_UNKNOWN", 404, "QR_UNKNOWN"),
        ("H03_QR_PAYLOAD_EXPIRED", 410, "QR_EXPIRED"),
        ("H03_QR_PAYLOAD_CONFLICT", 409, "QR_CONFLICT"),
    ],
    ids=["mock_03_invalido", "mock_04_desconocido", "mock_05_expirado", "mock_06_conflicto"],
)
def test_mock_03_a_06_resolve_errores_de_recuperacion(w3, env_name, status, code):
    resp = _resolve(w3, _env(env_name))
    assert resp.status_code == status, resp.text
    body = resp.json()
    assert body["code"] == code
    assert isinstance(body["message"], str)


def test_mock_07_resolve_con_payload_vacio_es_invalido(w3):
    resp = _resolve(w3, "")
    assert resp.status_code == 400, resp.text
    assert resp.json()["code"] == "QR_INVALID"


def test_mock_08_crear_pago_preserva_qr_id(w3, w2):
    qr = _resolved(w3, "H03_QR_PAYLOAD_FIXED")
    created = _created(w2, qr, qr["amount"])
    assert created["paymentId"] and created["reference"] and created["status"]
    assert created["qrId"] == qr["qrId"]


def test_mock_09_misma_clave_y_mismo_cuerpo_devuelve_el_mismo_pago(w3, w2):
    qr = _resolved(w3, "H03_QR_PAYLOAD_FIXED")
    key = str(uuid.uuid4())
    first = _pay(w2, qr["qrId"], qr["amount"], qr["currency"], key)
    second = _pay(w2, qr["qrId"], qr["amount"], qr["currency"], key)
    assert first.status_code in (200, 201), first.text
    assert second.status_code in (200, 201), second.text
    assert first.json()["paymentId"] == second.json()["paymentId"]


def test_mock_10_misma_clave_con_cuerpo_distinto_es_conflicto(w3, w2):
    qr = _resolved(w3, "H03_QR_PAYLOAD_OPEN")
    key = str(uuid.uuid4())
    first = _pay(w2, qr["qrId"], 10, qr["currency"], key)
    assert first.status_code in (200, 201), first.text
    second = _pay(w2, qr["qrId"], 11, qr["currency"], key)
    assert second.status_code == 409, second.text
    assert second.json()["code"] == "IDEMPOTENCY_CONFLICT"


@pytest.mark.parametrize("amount", [0, -1])
def test_mock_11_importe_no_positivo_en_monto_abierto_es_rechazado(w3, w2, amount):
    qr = _resolved(w3, "H03_QR_PAYLOAD_OPEN")
    resp = _pay(w2, qr["qrId"], amount, qr["currency"], str(uuid.uuid4()))
    assert resp.status_code == 422, resp.text
    assert resp.json()["code"] == "AMOUNT_INVALID"


def test_mock_12_consulta_de_estado_y_recibo(w3, w2):
    qr = _resolved(w3, "H03_QR_PAYLOAD_FIXED")
    created = _created(w2, qr, qr["amount"])
    status = w2.get(f"/payments/{created['paymentId']}")
    assert status.status_code == 200, status.text
    assert isinstance(status.json()["status"], str) and status.json()["status"]
    receipt = w2.get(f"/payments/{created['paymentId']}/receipt")
    assert receipt.status_code == 200, receipt.text
    assert isinstance(receipt.json(), dict)


def test_mock_13_pago_inexistente_devuelve_404_en_estado_y_recibo(w2):
    unknown = f"no-existe-{uuid.uuid4()}"
    assert w2.get(f"/payments/{unknown}").status_code == 404
    assert w2.get(f"/payments/{unknown}/receipt").status_code == 404


@pytest.mark.parametrize(
    "env_name,status,code",
    [("H03_QR_ID_EXPIRED", 410, "QR_EXPIRED"), ("H03_QR_ID_CONFLICT", 409, "QR_CONFLICT")],
    ids=["mock_14a_expirado", "mock_14b_conflicto"],
)
def test_mock_14_crear_pago_con_qr_expirado_o_en_conflicto(w2, env_name, status, code):
    resp = _pay(w2, _env(env_name), 10, "COP", str(uuid.uuid4()))
    assert resp.status_code == status, resp.text
    assert resp.json()["code"] == code


def test_mock_15_el_estado_no_cambia_sin_accion_manual(w3, w2):
    qr = _resolved(w3, "H03_QR_PAYLOAD_FIXED")
    created = _created(w2, qr, qr["amount"])
    before = w2.get(f"/payments/{created['paymentId']}").json()["status"]
    time.sleep(3)
    after = w2.get(f"/payments/{created['paymentId']}").json()["status"]
    assert before == after
```

# Specs Angular (Jasmine/Karma, supuesto T-4)

```typescript
// src/app/qr-pagos/qr-decoder.service.spec.ts
import { TestBed } from '@angular/core/testing';

import { QR_IMAGE_ENGINE, QrDecodeError, QrDecoderService, QrImageEngine } from './qr-decoder.service';

async function pngFile(): Promise<File> {
  const canvas = document.createElement('canvas');
  canvas.width = 8;
  canvas.height = 8;
  const blob = await new Promise<Blob>((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('toBlob falló'))), 'image/png'),
  );
  return new File([blob], 'qr.png', { type: 'image/png' });
}

describe('QrDecoderService (H03 CA-1)', () => {
  let decodeSpy: jasmine.Spy;

  function setup(available: boolean, impl: () => Promise<string | null>): QrDecoderService {
    decodeSpy = jasmine.createSpy('decode').and.callFake(impl);
    const engine: QrImageEngine = { available, decode: decodeSpy as unknown as QrImageEngine['decode'] };
    TestBed.configureTestingModule({
      providers: [QrDecoderService, { provide: QR_IMAGE_ENGINE, useValue: engine }],
    });
    return TestBed.inject(QrDecoderService);
  }

  it('FE-DEC-01 devuelve solo el texto del QR y entrega un ImageBitmap al motor', async () => {
    const svc = setup(true, async () => 'PAYLOAD-QR');
    const text = await svc.decode(await pngFile());
    expect(text).toBe('PAYLOAD-QR');
    expect(decodeSpy.calls.argsFor(0)[0] instanceof ImageBitmap).toBeTrue();
  });

  it('FE-DEC-02 rechaza un archivo que no es imagen sin invocar al motor', async () => {
    const svc = setup(true, async () => 'X');
    const file = new File(['hola'], 'nota.txt', { type: 'text/plain' });
    await expectAsync(svc.decode(file)).toBeRejectedWith(jasmine.objectContaining({ reason: 'NOT_IMAGE' }));
    expect(decodeSpy).not.toHaveBeenCalled();
  });

  it('FE-DEC-03 informa UNSUPPORTED si el motor no está disponible', async () => {
    const svc = setup(false, async () => 'X');
    await expectAsync(svc.decode(await pngFile())).toBeRejectedWith(
      jasmine.objectContaining({ reason: 'UNSUPPORTED' }),
    );
    expect(decodeSpy).not.toHaveBeenCalled();
  });

  it('FE-DEC-04 informa NO_QR si el motor no encuentra texto', async () => {
    const svc = setup(true, async () => null);
    await expectAsync(svc.decode(await pngFile())).toBeRejectedWith(jasmine.objectContaining({ reason: 'NO_QR' }));
  });

  it('FE-DEC-05 trata el texto vacío como NO_QR (borde)', async () => {
    const svc = setup(true, async () => '');
    await expectAsync(svc.decode(await pngFile())).toBeRejectedWith(jasmine.objectContaining({ reason: 'NO_QR' }));
  });

  it('FE-DEC-06 informa READ_FAILED si el motor lanza o la imagen es ilegible', async () => {
    const failing = setup(true, async () => {
      throw new Error('motor roto');
    });
    await expectAsync(failing.decode(await pngFile())).toBeRejectedWith(
      jasmine.objectContaining({ reason: 'READ_FAILED' }),
    );

    const corrupt = new File(['no-es-un-png'], 'roto.png', { type: 'image/png' });
    await expectAsync(failing.decode(corrupt)).toBeRejectedWith(jasmine.objectContaining({ reason: 'READ_FAILED' }));
    expect(new QrDecodeError('NO_QR').reason).toBe('NO_QR');
  });
});
```

```typescript
// src/app/qr-pagos/qr-api.service.spec.ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Observable } from 'rxjs';

import { QrApiService, newIdempotencyKey } from './qr-api.service';
import { ApiError } from './qr-pagos.models';

interface Captured<T> {
  value?: T;
  error?: unknown;
}

function capture<T>(obs: Observable<T>): Captured<T> {
  const out: Captured<T> = {};
  obs.subscribe({
    next: (v) => (out.value = v),
    error: (e: unknown) => (out.error = e),
  });
  return out;
}

describe('QrApiService (H03 CA-1, CA-3, CA-4, CA-6)', () => {
  let api: QrApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), QrApiService],
    });
    api = TestBed.inject(QrApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('FE-SVC-01 resolve envía solo el payload textual (sin imagen)', () => {
    const out = capture(api.resolve('PAYLOAD-QR'));
    const req = http.expectOne('/qrs/resolve');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ payload: 'PAYLOAD-QR' });
    expect(Object.keys(req.request.body as object)).toEqual(['payload']);
    expect(req.request.body instanceof Blob).toBeFalse();
    expect(req.request.body instanceof FormData).toBeFalse();
    req.flush({ qrId: 'q', merchant: { name: 'M' }, amountType: 'fixed', amount: 5, currency: 'COP' });
    expect(out.error).toBeUndefined();
  });

  it('FE-SVC-02 resolve normaliza QR fijo y QR de monto abierto', () => {
    const fixed = capture(api.resolve('A'));
    http.expectOne('/qrs/resolve').flush({
      qrId: 'qr_123',
      merchant: { name: 'Comercio Ejemplo' },
      amountType: 'fixed',
      amount: 12500,
      currency: 'COP',
    });
    expect(fixed.value).toEqual({
      qrId: 'qr_123',
      merchant: { name: 'Comercio Ejemplo' },
      amountType: 'fixed',
      amount: 12500,
      currency: 'COP',
    });

    const open = capture(api.resolve('B'));
    http.expectOne('/qrs/resolve').flush({
      qrId: 'qr_open',
      merchant: { name: 'Abierto' },
      amountType: 'open',
      currency: 'COP',
    });
    expect(open.value?.amountType).toBe('open');
    expect(open.value?.amount).toBeNull();
  });

  it('FE-SVC-03 resolve rechaza respuestas fuera de contrato con RESPONSE_INVALID', () => {
    const out = capture(api.resolve('A'));
    http.expectOne('/qrs/resolve').flush({ qrId: 'q', amountType: 'fixed', currency: 'COP' });
    expect(out.value).toBeUndefined();
    expect(out.error).toBeInstanceOf(ApiError);
    expect((out.error as ApiError).code).toBe('RESPONSE_INVALID');
  });

  it('FE-SVC-04 resolve traduce el cuerpo de error {code,message} a ApiError', () => {
    const out = capture(api.resolve('A'));
    http
      .expectOne('/qrs/resolve')
      .flush({ code: 'QR_EXPIRED', message: 'vencido' }, { status: 410, statusText: 'Gone' });
    const err = out.error as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(410);
    expect(err.code).toBe('QR_EXPIRED');
    expect(err.serviceMessage).toBe('vencido');
  });

  it('FE-SVC-05 un fallo de red se normaliza con status 0', () => {
    const out = capture(api.resolve('A'));
    http.expectOne('/qrs/resolve').error(new ProgressEvent('error'));
    const err = out.error as ApiError;
    expect(err.status).toBe(0);
    expect(err.code).toBeNull();
  });

  it('FE-SVC-06 createPayment conserva qrId y envía la cabecera de idempotencia', () => {
    const out = capture(api.createPayment({ qrId: 'qr_123', amount: 12500, currency: 'COP' }, 'clave-1'));
    const req = http.expectOne('/payments');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ qrId: 'qr_123', amount: 12500, currency: 'COP' });
    expect(req.request.headers.get('Idempotency-Key')).toBe('clave-1');
    req.flush({ paymentId: 'pay_456', reference: 'REF-0001', status: 'pending', qrId: 'qr_123' });
    expect(out.value).toEqual({ paymentId: 'pay_456', reference: 'REF-0001', status: 'pending', qrId: 'qr_123' });
  });

  it('FE-SVC-07 createPayment rechaza una respuesta sin referencia', () => {
    const out = capture(api.createPayment({ qrId: 'q', amount: 1, currency: 'COP' }, 'k'));
    http.expectOne('/payments').flush({ paymentId: 'pay_1', status: 'pending' });
    expect((out.error as ApiError).code).toBe('RESPONSE_INVALID');
  });

  it('FE-SVC-08 getPayment codifica el id en la URL y lee el estado', () => {
    const out = capture(api.getPayment('a/b c'));
    const req = http.expectOne('/payments/a%2Fb%20c');
    expect(req.request.method).toBe('GET');
    req.flush({ status: 'completed' });
    expect(out.value).toEqual({ status: 'completed' });
  });

  it('FE-SVC-09 getReceipt rechaza un recibo que no es un objeto', () => {
    const out = capture(api.getReceipt('pay_1'));
    http.expectOne('/payments/pay_1/receipt').flush([1, 2, 3]);
    expect((out.error as ApiError).code).toBe('RESPONSE_INVALID');

    const ok = capture(api.getReceipt('pay_1'));
    http.expectOne('/payments/pay_1/receipt').flush({ total: 5 });
    expect(ok.value).toEqual({ total: 5 });
  });

  it('FE-SVC-10 newIdempotencyKey genera claves no vacías y distintas', () => {
    const keys = new Set(Array.from({ length: 50 }, () => newIdempotencyKey()));
    expect(keys.size).toBe(50);
    keys.forEach((k) => expect(k.length).toBeGreaterThanOrEqual(32));
  });
});
```

```typescript
// src/app/qr-pagos/error-messages.spec.ts
import { guidanceFor, guidanceForDecode } from './error-messages';
import { QrDecodeError } from './qr-decoder.service';
import { ApiError } from './qr-pagos.models';

describe('error-messages (H03 CA-6)', () => {
  it('FE-ERR-01 cada código de negocio produce el título y la acción esperados', () => {
    const cases: Array<[number, string, string, string]> = [
      [400, 'QR_INVALID', 'El código QR no es válido', 'choose-another-qr'],
      [404, 'QR_UNKNOWN', 'QR no reconocido', 'choose-another-qr'],
      [410, 'QR_EXPIRED', 'El QR expiró', 'choose-another-qr'],
      [409, 'QR_CONFLICT', 'Los datos del comercio o del importe cambiaron', 'revalidate'],
      [422, 'AMOUNT_INVALID', 'Importe no válido', 'none'],
      [409, 'IDEMPOTENCY_CONFLICT', 'Solicitud repetida con datos distintos', 'none'],
      [413, 'PAYLOAD_TOO_LARGE', 'El contenido del QR es demasiado grande', 'choose-another-qr'],
      [200, 'RESPONSE_INVALID', 'Respuesta inesperada del servicio', 'none'],
    ];
    for (const [status, code, title, action] of cases) {
      const g = guidanceFor(new ApiError(status, code, null), 'resolve');
      expect(g.title).withContext(code).toBe(title);
      expect(g.action).withContext(code).toBe(action);
    }
  });

  it('FE-ERR-02 el conflicto de comercio/importe pide revalidar y no confirmar con datos previos', () => {
    const g = guidanceFor(new ApiError(409, 'QR_CONFLICT', null), 'payment');
    expect(g.action).toBe('revalidate');
    expect(g.detail).toContain('No confirmes con los datos anteriores');
  });

  it('FE-ERR-03 un 413 sin código se reconoce por el estado HTTP', () => {
    const g = guidanceFor(new ApiError(413, null, null), 'resolve');
    expect(g.title).toBe('El contenido del QR es demasiado grande');
    expect(g.action).toBe('choose-another-qr');
  });

  it('FE-ERR-04 401 y 403 producen un mensaje genérico de autorización', () => {
    for (const status of [401, 403]) {
      expect(guidanceFor(new ApiError(status, null, 'secreto'), 'payment').title).toBe('No tienes autorización');
    }
  });

  it('FE-ERR-05 el 404 solo es "pago/recibo no encontrado" en consultas de estado o recibo', () => {
    expect(guidanceFor(new ApiError(404, null, null), 'status').title).toBe('No se encontró el pago o el recibo');
    expect(guidanceFor(new ApiError(404, null, null), 'receipt').title).toBe('No se encontró el pago o el recibo');
    expect(guidanceFor(new ApiError(404, null, null), 'resolve').title).toBe('No se pudo completar la operación');
  });

  it('FE-ERR-06 sin conexión en un pago indica que se reutiliza la misma solicitud', () => {
    const pay = guidanceFor(new ApiError(0, null, null), 'payment');
    expect(pay.title).toBe('Sin conexión con el servicio');
    expect(pay.detail).toContain('se reutiliza la misma solicitud');
    const other = guidanceFor(new ApiError(0, null, null), 'resolve');
    expect(other.detail).not.toContain('se reutiliza la misma solicitud');
  });

  it('FE-ERR-07 un 5xx se muestra como fallo del servicio', () => {
    expect(guidanceFor(new ApiError(503, null, null), 'payment').title).toBe(
      'El servicio no pudo procesar la solicitud',
    );
  });

  it('FE-ERR-08 un código desconocido muestra el mensaje del servicio o el código', () => {
    expect(guidanceFor(new ApiError(418, 'X_RARO', 'texto del servicio'), 'resolve').detail).toBe('texto del servicio');
    expect(guidanceFor(new ApiError(418, 'X_RARO', null), 'resolve').detail).toContain('X_RARO');
    expect(guidanceFor(new ApiError(418, 'X_RARO', 'texto del servicio'), 'resolve').serviceMessage).toBe(
      'texto del servicio',
    );
  });

  it('FE-ERR-09 los errores de lectura local tienen su guía y no culpan al servicio', () => {
    expect(guidanceForDecode(new QrDecodeError('UNSUPPORTED')).title).toBe(
      'Tu navegador no puede leer QR desde imágenes',
    );
    expect(guidanceForDecode(new QrDecodeError('NOT_IMAGE')).title).toBe('El archivo no es una imagen');
    expect(guidanceForDecode(new QrDecodeError('NO_QR')).title).toBe('No se encontró un QR en la imagen');
    expect(guidanceForDecode(new QrDecodeError('READ_FAILED')).title).toBe('No se pudo leer la imagen');
    expect(guidanceForDecode(new QrDecodeError('NO_QR')).serviceMessage).toBeNull();
  });
});
```

```typescript
// src/app/qr-pagos/payment-history.service.spec.ts
import { TestBed } from '@angular/core/testing';

import { PaymentHistoryService } from './payment-history.service';
import { HistoryEntry } from './qr-pagos.models';

const KEY = 'merchantQrPayments.history';

function entry(id: string, over: Partial<HistoryEntry> = {}): HistoryEntry {
  return {
    paymentId: id,
    reference: `REF-${id}`,
    status: 'pending',
    qrId: 'qr_123',
    merchantName: 'Comercio Ejemplo',
    amount: 12500,
    currency: 'COP',
    registeredAtLocal: '2026-11-06T10:00:00.000Z',
    ...over,
  };
}

describe('PaymentHistoryService (H03 CA-5)', () => {
  function create(): PaymentHistoryService {
    TestBed.configureTestingModule({ providers: [PaymentHistoryService] });
    return TestBed.inject(PaymentHistoryService);
  }

  beforeEach(() => localStorage.removeItem(KEY));
  afterEach(() => localStorage.removeItem(KEY));

  it('FE-STO-01 add guarda con schemaVersion 1 y la fecha local registrada', () => {
    const svc = create();
    expect(svc.add(entry('pay_1'))).toBeTrue();
    const stored = JSON.parse(localStorage.getItem(KEY) as string);
    expect(stored.schemaVersion).toBe(1);
    expect(stored.entries.length).toBe(1);
    expect(stored.entries[0].registeredAtLocal).toBe('2026-11-06T10:00:00.000Z');
    expect(svc.entries().map((e) => e.paymentId)).toEqual(['pay_1']);
  });

  it('FE-STO-02 deduplica por paymentId y deja la entrada más reciente primero', () => {
    const svc = create();
    svc.add(entry('pay_1'));
    svc.add(entry('pay_2'));
    svc.add(entry('pay_1', { status: 'completed' }));
    expect(svc.entries().map((e) => e.paymentId)).toEqual(['pay_1', 'pay_2']);
    expect(svc.entries()[0].status).toBe('completed');
  });

  it('FE-STO-03 ignora entradas corruptas sin romper la lectura', () => {
    localStorage.setItem(
      KEY,
      JSON.stringify({
        schemaVersion: 1,
        entries: [entry('pay_ok'), { paymentId: 1 }, null, 'texto', entry('pay_fecha', { registeredAtLocal: 'no-fecha' })],
      }),
    );
    const svc = create();
    expect(svc.entries().map((e) => e.paymentId)).toEqual(['pay_ok']);
  });

  it('FE-STO-04 con JSON ilegible no sobrescribe y add devuelve false', () => {
    localStorage.setItem(KEY, '{basura');
    const svc = create();
    expect(svc.entries()).toEqual([]);
    expect(svc.add(entry('pay_1'))).toBeFalse();
    expect(localStorage.getItem(KEY)).toBe('{basura');
  });

  it('FE-STO-05 con un esquema ajeno no sobrescribe los datos', () => {
    const foreign = JSON.stringify({ schemaVersion: 2, entries: [{ otro: true }] });
    localStorage.setItem(KEY, foreign);
    const svc = create();
    expect(svc.add(entry('pay_1'))).toBeFalse();
    expect(svc.update('pay_1', { status: 'x' })).toBeFalse();
    expect(localStorage.getItem(KEY)).toBe(foreign);
  });

  it('FE-STO-06 el evento storage de la clave refresca la lista (otra pestaña)', () => {
    const svc = create();
    expect(svc.entries()).toEqual([]);
    localStorage.setItem(KEY, JSON.stringify({ schemaVersion: 1, entries: [entry('pay_otra_pestana')] }));
    window.dispatchEvent(new StorageEvent('storage', { key: KEY }));
    expect(svc.entries().map((e) => e.paymentId)).toEqual(['pay_otra_pestana']);
  });

  it('FE-STO-07 el evento storage de otra clave no refresca la lista', () => {
    const svc = create();
    localStorage.setItem(KEY, JSON.stringify({ schemaVersion: 1, entries: [entry('pay_1')] }));
    window.dispatchEvent(new StorageEvent('storage', { key: 'otra.clave' }));
    expect(svc.entries()).toEqual([]);
  });

  it('FE-STO-08 si el almacenamiento falla (cuota) add devuelve false y no cambia la lista', () => {
    const svc = create();
    spyOn(Storage.prototype, 'setItem').and.throwError('QuotaExceededError');
    expect(svc.add(entry('pay_1'))).toBeFalse();
    expect(svc.entries()).toEqual([]);
  });

  it('FE-STO-09 update cambia solo el estado de la entrada indicada', () => {
    const svc = create();
    svc.add(entry('pay_1'));
    svc.add(entry('pay_2'));
    expect(svc.update('pay_1', { status: 'completed' })).toBeTrue();
    const byId = Object.fromEntries(svc.entries().map((e) => [e.paymentId, e]));
    expect(byId['pay_1'].status).toBe('completed');
    expect(byId['pay_1'].registeredAtLocal).toBe('2026-11-06T10:00:00.000Z');
    expect(byId['pay_2'].status).toBe('pending');
  });
});
```

```typescript
// src/app/qr-pagos/qr-pago.component.spec.ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, TestRequest, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { PaymentHistoryService } from './payment-history.service';
import { QrApiService } from './qr-api.service';
import { QrDecoderService } from './qr-decoder.service';
import { QrPagoComponent } from './qr-pago.component';

const KEY = 'merchantQrPayments.history';
const PAYLOAD = 'PAYLOAD-QR';
const QR_FIXED = {
  qrId: 'qr_123',
  merchant: { name: 'Comercio Ejemplo' },
  amountType: 'fixed',
  amount: 12500,
  currency: 'COP',
};
const QR_OPEN = { qrId: 'qr_open', merchant: { name: 'Comercio Abierto' }, amountType: 'open', currency: 'COP' };
const PAYMENT = { paymentId: 'pay_456', reference: 'REF-0001', status: 'pending', qrId: 'qr_123' };

describe('QrPagoComponent (H03 CA-1…CA-6)', () => {
  let fixture: ComponentFixture<QrPagoComponent>;
  let comp: QrPagoComponent;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.removeItem(KEY);
    TestBed.configureTestingModule({
      imports: [QrPagoComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        QrApiService,
        PaymentHistoryService,
        { provide: QrDecoderService, useValue: { decode: async () => PAYLOAD } },
      ],
    });
    fixture = TestBed.createComponent(QrPagoComponent);
    comp = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => {
    http.verify();
    localStorage.removeItem(KEY);
  });

  function fileEvent(): Event {
    const file = new File(['x'], 'qr.png', { type: 'image/png' });
    return { target: { files: [file], value: 'x' } } as unknown as Event;
  }

  async function loadQr(body: unknown): Promise<void> {
    await comp.onFileSelected(fileEvent());
    http.expectOne('/qrs/resolve').flush(body);
    fixture.detectChanges();
  }

  async function loadQrError(status: number, body: unknown): Promise<void> {
    await comp.onFileSelected(fileEvent());
    http.expectOne('/qrs/resolve').flush(body, { status, statusText: 'err' });
    fixture.detectChanges();
  }

  function pay(): TestRequest {
    comp.confirm();
    return http.expectOne('/payments');
  }

  function text(): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  function submitButton(): HTMLButtonElement {
    return (fixture.nativeElement as HTMLElement).querySelector('button[type="submit"]') as HTMLButtonElement;
  }

  function storedEntries(): Array<Record<string, unknown>> {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw).entries as Array<Record<string, unknown>>) : [];
  }

  it('FE-PAGO-01 tras elegir el archivo, a W3 viaja solo {payload}', async () => {
    await comp.onFileSelected(fileEvent());
    const req = http.expectOne('/qrs/resolve');
    expect(req.request.body).toEqual({ payload: PAYLOAD });
    req.flush(QR_FIXED);
  });

  it('FE-PAGO-02 muestra comercio e importe antes de confirmar y no crea el pago', async () => {
    await loadQr(QR_FIXED);
    expect(comp.phase()).toBe('review');
    expect(text()).toContain('Comercio Ejemplo');
    expect(text()).toContain('12500 COP');
    http.expectNone('/payments');
  });

  it('FE-PAGO-03 monto abierto: confirmar solo está habilitado con importe > 0', async () => {
    await loadQr(QR_OPEN);
    const cases: Array<[number | null, boolean]> = [
      [null, false],
      [0, false],
      [-5, false],
      [Number.NaN, false],
      [Number.POSITIVE_INFINITY, false],
      [10, true],
    ];
    for (const [value, enabled] of cases) {
      comp.amountCtrl.setValue(value);
      fixture.detectChanges();
      expect(comp.canConfirm()).withContext(String(value)).toBe(enabled);
      expect(submitButton().disabled).withContext(String(value)).toBe(!enabled);
    }
  });

  it('FE-PAGO-04 monto abierto: mensajes de importe vacío, cero y negativo', async () => {
    await loadQr(QR_OPEN);
    expect(comp.amountError()).toBeNull();
    comp.amountCtrl.markAsTouched();
    expect(comp.amountError()).toBe('Ingresa el importe a pagar.');
    comp.amountCtrl.setValue(0);
    expect(comp.amountError()).toBe('El importe debe ser un número mayor que 0.');
    comp.amountCtrl.setValue(-5);
    expect(comp.amountError()).toBe('El importe debe ser un número mayor que 0.');
    comp.amountCtrl.setValue(10);
    expect(comp.amountError()).toBeNull();
  });

  it('FE-PAGO-05 confirm sin importe válido no envía ninguna petición', async () => {
    await loadQr(QR_OPEN);
    comp.confirm();
    comp.amountCtrl.setValue(0);
    comp.confirm();
    http.expectNone('/payments');
    expect(comp.phase()).toBe('review');
  });

  it('FE-PAGO-06 QR fijo con importe no válido no se puede confirmar (borde)', async () => {
    await loadQr({ ...QR_FIXED, amount: 0 });
    expect(comp.canConfirm()).toBeFalse();
    expect(text()).toContain('El QR trae un importe no válido; no se puede confirmar.');
    comp.confirm();
    http.expectNone('/payments');

    await loadQr({ ...QR_FIXED, amount: null });
    expect(comp.canConfirm()).toBeFalse();
  });

  it('FE-PAGO-07 el pago lleva el qrId de W3, importe, moneda y la clave de idempotencia', async () => {
    await loadQr(QR_FIXED);
    const req = pay();
    expect(req.request.body).toEqual({ qrId: 'qr_123', amount: 12500, currency: 'COP' });
    expect(req.request.headers.get('Idempotency-Key')).toBeTruthy();
    req.flush(PAYMENT);
  });

  it('FE-PAGO-08 doble confirmación inmediata genera una sola petición', async () => {
    await loadQr(QR_FIXED);
    comp.confirm();
    comp.confirm();
    const req = http.expectOne('/payments');
    expect(comp.phase()).toBe('submitting');
    req.flush(PAYMENT);
  });

  it('FE-PAGO-09 el reintento tras fallo de red reutiliza la clave; un importe nuevo genera otra', async () => {
    await loadQr(QR_OPEN);
    comp.amountCtrl.setValue(10);
    const first = pay();
    const key1 = first.request.headers.get('Idempotency-Key');
    first.error(new ProgressEvent('error'));
    expect(comp.phase()).toBe('review');

    const retry = pay();
    expect(retry.request.headers.get('Idempotency-Key')).toBe(key1);
    retry.error(new ProgressEvent('error'));

    comp.amountCtrl.setValue(20);
    const changed = pay();
    expect(changed.request.headers.get('Idempotency-Key')).not.toBe(key1);
    expect((changed.request.body as { amount: number }).amount).toBe(20);
    changed.flush(PAYMENT);
  });

  it('FE-PAGO-10 IDEMPOTENCY_CONFLICT descarta la clave: el siguiente intento usa otra', async () => {
    await loadQr(QR_FIXED);
    const first = pay();
    const key1 = first.request.headers.get('Idempotency-Key');
    first.flush({ code: 'IDEMPOTENCY_CONFLICT', message: 'm' }, { status: 409, statusText: 'Conflict' });
    expect(comp.phase()).toBe('review');
    expect(comp.error()?.title).toBe('Solicitud repetida con datos distintos');

    const second = pay();
    expect(second.request.headers.get('Idempotency-Key')).not.toBe(key1);
    second.flush(PAYMENT);
  });

  it('FE-PAGO-11 un pago exitoso se guarda en el historial local y no dispara más peticiones', async () => {
    await loadQr(QR_FIXED);
    pay().flush(PAYMENT);
    fixture.detectChanges();
    expect(comp.phase()).toBe('success');
    expect(text()).toContain('REF-0001');
    const entries = storedEntries();
    expect(entries.length).toBe(1);
    expect(entries[0]['paymentId']).toBe('pay_456');
    expect(entries[0]['merchantName']).toBe('Comercio Ejemplo');
    expect(entries[0]['amount']).toBe(12500);
    expect(entries[0]['qrId']).toBe('qr_123');
    const registered = Date.parse(entries[0]['registeredAtLocal'] as string);
    expect(Math.abs(Date.now() - registered)).toBeLessThan(60_000);
    http.expectNone(() => true);
  });

  it('FE-PAGO-12 el estado solo se consulta a W2 por acción manual y se refleja', async () => {
    await loadQr(QR_FIXED);
    pay().flush(PAYMENT);
    comp.refreshStatus();
    comp.refreshStatus(); // segunda llamada ignorada mientras hay una en curso
    const req = http.expectOne('/payments/pay_456');
    expect(req.request.method).toBe('GET');
    req.flush({ status: 'completed' });
    expect(comp.payment()?.status).toBe('completed');
    expect(storedEntries()[0]['status']).toBe('completed');

    comp.refreshStatus();
    http.expectOne('/payments/pay_456').flush({}, { status: 404, statusText: 'Not Found' });
    expect(comp.error()?.title).toBe('No se encontró el pago o el recibo');
  });

  const resolveErrors: Array<[number, string, string]> = [
    [400, 'QR_INVALID', 'El código QR no es válido'],
    [404, 'QR_UNKNOWN', 'QR no reconocido'],
    [410, 'QR_EXPIRED', 'El QR expiró'],
    [409, 'QR_CONFLICT', 'Los datos del comercio o del importe cambiaron'],
  ];
  for (const [status, code, title] of resolveErrors) {
    it(`FE-PAGO-13 resolve ${code}: muestra la guía y no permite pagar`, async () => {
      await loadQrError(status, { code, message: 'detalle' });
      expect(comp.phase()).toBe('idle');
      expect(comp.resolved()).toBeNull();
      expect(comp.error()?.title).toBe(title);
      expect(text()).toContain(title);
      comp.confirm();
      http.expectNone('/payments');
      expect(storedEntries()).toEqual([]);
    });
  }

  it('FE-PAGO-14 QR_EXPIRED al crear el pago descarta la revisión y no guarda nada', async () => {
    await loadQr(QR_FIXED);
    pay().flush({ code: 'QR_EXPIRED', message: 'm' }, { status: 410, statusText: 'Gone' });
    expect(comp.phase()).toBe('idle');
    expect(comp.resolved()).toBeNull();
    expect(comp.error()?.title).toBe('El QR expiró');
    expect(storedEntries()).toEqual([]);
  });

  it('FE-PAGO-15 QR_CONFLICT al crear el pago pide revalidar y reenvía el mismo payload a W3', async () => {
    await loadQr(QR_FIXED);
    pay().flush({ code: 'QR_CONFLICT', message: 'm' }, { status: 409, statusText: 'Conflict' });
    expect(comp.error()?.action).toBe('revalidate');
    expect(comp.resolved()).toBeNull();
    comp.confirm();
    http.expectNone('/payments');

    comp.revalidate();
    const again = http.expectOne('/qrs/resolve');
    expect(again.request.body).toEqual({ payload: PAYLOAD });
    again.flush({ ...QR_FIXED, amount: 13000 });
    expect(comp.phase()).toBe('review');
    expect(comp.amountToPay()).toBe(13000);
  });

  it('FE-PAGO-16 una respuesta de pago fuera de contrato no se muestra como pago creado', async () => {
    await loadQr(QR_FIXED);
    pay().flush({ foo: 'bar' });
    expect(comp.phase()).toBe('review');
    expect(comp.payment()).toBeNull();
    expect(comp.error()?.title).toBe('Respuesta inesperada del servicio');
    expect(storedEntries()).toEqual([]);
  });

  it('FE-PAGO-17 si el historial no se puede guardar, el pago sigue siendo exitoso y se avisa', async () => {
    await loadQr(QR_FIXED);
    localStorage.setItem(KEY, 'basura');
    pay().flush(PAYMENT);
    fixture.detectChanges();
    expect(comp.phase()).toBe('success');
    expect(comp.historyWarning()).toBeTrue();
    expect(text()).toContain('no se pudo guardar en el historial local');
    expect(localStorage.getItem(KEY)).toBe('basura');
  });

  it('FE-PAGO-18 el mensaje del servicio se muestra como texto plano (sin HTML)', async () => {
    await loadQrError(404, { code: 'X_OTRO', message: '<img src=x onerror=alert(1)>' });
    const root = fixture.nativeElement as HTMLElement;
    expect(root.querySelector('.alert img')).toBeNull();
    expect(text()).toContain('<img src=x onerror=alert(1)>');
  });

  it('FE-PAGO-19 la pantalla de éxito no habla de webhooks ni de notificaciones automáticas', async () => {
    await loadQr(QR_FIXED);
    pay().flush(PAYMENT);
    fixture.detectChanges();
    expect(text()).toContain('El estado no cambia solo');
    expect(text()).not.toMatch(/webhook|notificaci[oó]n autom/i);
  });
});
```

```typescript
// src/app/qr-pagos/historial.component.spec.ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { HistorialComponent } from './historial.component';
import { PaymentHistoryService } from './payment-history.service';
import { QrApiService } from './qr-api.service';
import { HistoryEntry } from './qr-pagos.models';

const KEY = 'merchantQrPayments.history';

function entry(id: string, over: Partial<HistoryEntry> = {}): HistoryEntry {
  return {
    paymentId: id,
    reference: `REF-${id}`,
    status: 'pending',
    qrId: 'qr_123',
    merchantName: 'Comercio Ejemplo',
    amount: 12500,
    currency: 'COP',
    registeredAtLocal: '2026-11-06T10:00:00.000Z',
    ...over,
  };
}

describe('HistorialComponent (H03 CA-4, CA-5)', () => {
  let fixture: ComponentFixture<HistorialComponent>;
  let comp: HistorialComponent;
  let http: HttpTestingController;

  const seed = (entries: unknown[]): void =>
    localStorage.setItem(KEY, JSON.stringify({ schemaVersion: 1, entries }));

  function create(): void {
    fixture = TestBed.createComponent(HistorialComponent);
    comp = fixture.componentInstance;
    fixture.detectChanges();
  }

  const root = (): HTMLElement => fixture.nativeElement as HTMLElement;
  const text = (): string => root().textContent ?? '';

  beforeEach(() => {
    localStorage.removeItem(KEY);
    TestBed.configureTestingModule({
      imports: [HistorialComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([]), QrApiService, PaymentHistoryService],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    localStorage.removeItem(KEY);
  });

  it('FE-HIST-01 sin pagos muestra el estado vacío con enlace a pagar', () => {
    create();
    expect(text()).toContain('Aún no hay pagos QR iniciados desde esta aplicación');
    expect(root().querySelector('a[href="/pagar-qr"]')).not.toBeNull();
    expect(root().querySelector('table')).toBeNull();
  });

  it('FE-HIST-02 la columna se llama «Fecha local registrada» y conserva el ISO guardado', () => {
    seed([entry('pay_1')]);
    create();
    const headers = Array.from(root().querySelectorAll('th')).map((th) => th.textContent?.trim());
    expect(headers).toContain('Fecha local registrada');
    expect(headers).not.toContain('Fecha de pago');
    expect(root().querySelector('time')?.getAttribute('datetime')).toBe('2026-11-06T10:00:00.000Z');
    expect(text()).toContain('hora de este dispositivo');
  });

  it('FE-HIST-03 el filtro de texto busca por referencia, comercio e ID sin distinguir mayúsculas', () => {
    seed([
      entry('pay_1', { merchantName: 'Panadería Sol' }),
      entry('pay_2', { merchantName: 'Cafetería Luna' }),
      entry('pay_3', { merchantName: 'Librería Mar' }),
    ]);
    create();
    comp.onQuery({ target: { value: 'LUNA' } } as unknown as Event);
    expect(comp.filtered().map((e) => e.paymentId)).toEqual(['pay_2']);
    comp.onQuery({ target: { value: 'ref-pay_3' } } as unknown as Event);
    expect(comp.filtered().map((e) => e.paymentId)).toEqual(['pay_3']);
    comp.onQuery({ target: { value: 'pay_1' } } as unknown as Event);
    expect(comp.filtered().map((e) => e.paymentId)).toEqual(['pay_1']);
    fixture.detectChanges();
    expect(text()).toContain('Mostrando 1 de 3 pagos.');
  });

  it('FE-HIST-04 el filtro de estado es local: no emite peticiones', () => {
    seed([entry('pay_1', { status: 'pending' }), entry('pay_2', { status: 'completed' })]);
    create();
    expect(comp.statuses()).toEqual(['completed', 'pending']);
    comp.onStatus({ target: { value: 'completed' } } as unknown as Event);
    expect(comp.filtered().map((e) => e.paymentId)).toEqual(['pay_2']);
    http.expectNone(() => true);
  });

  it('FE-HIST-05 sin coincidencias avisa y «Limpiar filtros» restablece la lista (borde)', () => {
    seed([entry('pay_1')]);
    create();
    comp.onQuery({ target: { value: 'nada-coincide' } } as unknown as Event);
    fixture.detectChanges();
    expect(text()).toContain('Ningún pago coincide con el filtro.');
    comp.clearFilters();
    fixture.detectChanges();
    expect(comp.filtered().length).toBe(1);
    expect(text()).not.toContain('Ningún pago coincide con el filtro.');
  });

  it('FE-HIST-06 las entradas corruptas del almacenamiento no rompen la vista', () => {
    seed([entry('pay_ok'), { basura: true }, null, 42]);
    create();
    expect(comp.entries().map((e) => e.paymentId)).toEqual(['pay_ok']);
    expect(text()).toContain('Mostrando 1 de 1 pagos.');
  });

  it('FE-HIST-07 «Actualizar estado» consulta W2 una vez, actualiza la lista y guarda el estado', () => {
    seed([entry('pay_1')]);
    create();
    const target = comp.entries()[0];
    comp.refresh(target);
    comp.refresh(target); // ignorada mientras hay una consulta en curso
    const req = http.expectOne('/payments/pay_1');
    expect(req.request.method).toBe('GET');
    req.flush({ status: 'completed' });
    expect(comp.entries()[0].status).toBe('completed');
    expect(JSON.parse(localStorage.getItem(KEY) as string).entries[0].status).toBe('completed');
    expect(comp.busyKey()).toBeNull();
  });

  it('FE-HIST-08 «Ver recibo» muestra cada campo del recibo tal como llega', () => {
    seed([entry('pay_1')]);
    create();
    comp.viewReceipt(comp.entries()[0]);
    http.expectOne('/payments/pay_1/receipt').flush({ reference: 'REF-1', total: 5, nested: { a: 1 }, nulo: null });
    const fields = Object.fromEntries((comp.receipt()?.fields ?? []).map((f) => [f.label, f.value]));
    expect(fields).toEqual({ reference: 'REF-1', total: '5', nested: '{"a":1}', nulo: '' });
    fixture.detectChanges();
    expect(text()).toContain('Recibo del pago REF-pay_1');
    comp.closeReceipt();
    expect(comp.receipt()).toBeNull();
  });

  it('FE-HIST-09 un recibo inexistente muestra la guía de 404 y no abre el panel', () => {
    seed([entry('pay_1')]);
    create();
    comp.viewReceipt(comp.entries()[0]);
    http.expectOne('/payments/pay_1/receipt').flush({}, { status: 404, statusText: 'Not Found' });
    expect(comp.receipt()).toBeNull();
    expect(comp.error()?.title).toBe('No se encontró el pago o el recibo');
    expect(comp.busyKey()).toBeNull();
  });
});
```

**Nota final.** Nada de lo anterior se ha ejecutado. Quien lo ejecute debe adjuntar las salidas reales en `evidencia/` y completar la tabla de §9. Mientras tanto, todos los criterios CA-1 a CA-7 permanecen **NO EJECUTADO** y ninguno puede darse por cumplido.