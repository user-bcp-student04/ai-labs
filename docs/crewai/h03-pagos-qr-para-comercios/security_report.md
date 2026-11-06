# security_report.md

**H03 · Pagos QR para comercios — Informe de revisión de seguridad**
Fecha del informe: 2026-11-06 · Rol: Revisor de seguridad de aplicaciones

---

## 0. Cómo leer este informe

Cada afirmación lleva uno de tres sellos, para no mezclar lo detectado con lo propuesto ni con lo verificado:

| Sello | Significado |
|---|---|
| **DETECTADO** | Riesgo observado por lectura del código y los documentos entregados. La evidencia es una cita o un `grep` reproducible. |
| **PROPUESTO** | Corrección o comprobación que yo sugiero. No está aplicada ni probada. |
| **VERIFICADO** | Resultado de un comando ejecutado, con salida real adjunta. |

**Estado global: no hay nada VERIFICADO.** No ejecuté ningún comando, prueba, compilación ni consulta a PyPI/OSV. Lo único realizado es la **revisión estática manual** de los artefactos de los pasos anteriores (`user_story.md`, `backend_spec.md`, `frontend_spec.md`, `testing_report.md` y el código y las pruebas incluidos). Todo "Resultado esperado" de este informe es una expectativa, no un resultado.

**Limitaciones de la revisión**
- No tengo el repositorio real, los documentos OpenSpec (`design.md`, `spec.md`), el mock W2/W3 ni el árbol de archivos. El contrato W2/W3 (P-1) es **supuesto**. Los hallazgos que dependen de él están marcados "condicional".
- Los archivos se entregaron como bloques de código sin numeración de líneas. La **ubicación** se da como archivo + símbolo (función, método o plantilla). Cada hallazgo incluye un `grep -n` para obtener la línea exacta en el repositorio real.
- Las severidades son **provisionales**. Dependen de P-1 (contrato), P-4 (unidad del importe), P-6 (límite de payload), P-7 (rol de comercio) y P-8 (credenciales).
- No recibí entrega de un rol de Seguridad previo. Revisé directamente los artefactos de Arquitectura, Backend, Frontend y Pruebas.

---

## 1. Resumen priorizado

| ID | Sev. (provisional) | Hallazgo | Archivo principal | Estado |
|---|---|---|---|---|
| H-01 | **Alta (condicional)** | Sin identidad ni autorización demostrada sobre estado y recibo de pagos de otras personas; el rol de comercio no existe | `qr-api.service.ts`, `historial.component.ts` | DETECTADO |
| H-02 | **Alta (condicional)** | Importe y moneda los decide el cliente también en QR de importe fijo; sin prueba de que el servidor los fuerce | `qr-pago.component.ts` | DETECTADO |
| H-03 | **Media** | La clave de idempotencia solo vive en memoria: puede haber cobro duplicado tras recargar o volver a elegir el mismo QR | `qr-pago.component.ts` | DETECTADO |
| H-04 | **Media** | El recibo se muestra "tal cual", sin lista de campos permitidos: exposición de datos sensibles | `historial.component.ts` | DETECTADO |
| H-05 | **Media/Baja** | Historial en `localStorage` en claro, sin identidad, sin opción de borrado y sin CSP definida | `payment-history.service.ts` | DETECTADO |
| H-06 | **Baja** | `paymentId` sin validar de formato y usado en una ruta de URL (segmentos `.`/`..`) | `qr-pagos.config.ts`, `payment-history.service.ts`, `qr-api.service.ts` | DETECTADO |
| H-07 | **Baja (sin verificar)** | Dependencias con pines no verificados contra PyPI/OSV; sin hashes ni lockfile revisado | `api/requirements.txt` | DETECTADO |
| H-08 | **Baja** | Backend base: el handler refleja `detail` en 4xx sin mapear y nombres de campo del cliente; el log incluye la ruta sin sanear | `api/app/errors.py` | DETECTADO |
| H-09 | **Baja** | Documentación OpenAPI expuesta por defecto y `LOG_LEVEL` sin validar | `api/app/main.py`, `config.py` | DETECTADO |
| H-10 | **Baja** | Sin límite de tamaño de archivo ni de payload en el cliente (P-6) | `qr-decoder.service.ts`, `qr-api.service.ts` | DETECTADO |
| H-11 | **Informativa** | Orígenes W2/W3 configurables sin lista permitida; CORS y CSP sin definir; sin credenciales | `qr-pagos.config.ts`, `main.py` | DETECTADO |

No encontré inyección SQL ni de comandos, secretos embebidos ni XSS en el código entregado. Ver §4. Esa conclusión viene de lectura, no de ejecución.

---

## 2. Hallazgos

### H-01 · Identidad y autorización sobre pagos y recibos de otras personas (condicional a P-1, P-7, P-8)

- **Estado:** DETECTADO (riesgo). El control efectivo no es verificable con la información disponible.
- **Archivos y ubicación:**
  - `src/app/qr-pagos/qr-api.service.ts` → `getPayment()`, `getReceipt()`. Ninguna petición lleva credenciales ni identidad.
  - `src/app/qr-pagos/qr-pagos.config.ts` → `w2PaymentStatusPath`, `w2PaymentReceiptPath`.
  - `src/app/qr-pagos/historial.component.ts` → `refresh()`, `viewReceipt()`.
  - `src/app/qr-pagos/payment-history.service.ts` → el historial no está asociado a ninguna identidad.
- **Evidencia:**
  - `getPayment(paymentId)` hace `GET /payments/{paymentId}` y `getReceipt` hace `GET /payments/{paymentId}/receipt`. No hay `Authorization`, `withCredentials` ni interceptor.
  - `frontend_spec.md` §12: "El frontend no envía credenciales." P-8 (¿el mock requiere credenciales?) sigue abierto.
  - `user_story.md` P-7: el objetivo habla de que "el comercio" consulte referencia, estado y recibo, pero el historial es local a quien paga. No existe rol de comercio.
  - `testing_report.md`: los `MOCK-12` y `MOCK-13` solo comprueban "existe / no existe". **Ninguna prueba cubre el acceso con una identidad distinta a la que creó el pago.**
  - Reproducir: `grep -n "getPayment\|getReceipt\|withCredentials\|Authorization" src/app/qr-pagos/qr-api.service.ts`
- **Impacto:**
  - Si W2 no valida pertenencia (BOLA/IDOR), cualquiera que conozca o adivine un `paymentId` lee estado y recibo ajenos, con posible exposición de datos del pagador o del comercio.
  - Un `paymentId` también puede salir de `localStorage` manipulado o de otro perfil del navegador. El cliente no puede limitar esto.
  - Si el criterio "el comercio consulta referencia, estado y recibo" se implementa más adelante, hará falta autorización por comercio. Hoy cualquier vista de comercio dependería solo de ocultar controles en la interfaz.
- **Corrección propuesta (PROPUESTO):**
  1. **Servidor (W2, fuera del alcance del frontend):**
     - La identidad sale de un token verificado en el servidor, nunca de un campo enviado por el cliente.
     - `GET /payments/{id}` y `/receipt` devuelven **404** (no 403) si el pago no pertenece al solicitante, para no confirmar su existencia.
     - Los pagos se listan o consultan por comercio solo con un rol de comercio verificado.
  2. **Cliente:** cuando se defina el esquema de credenciales (P-8), añadirlo en un único interceptor:
     ```typescript
     // PROPUESTO — el esquema real depende de P-8; no inventar cabeceras
     provideHttpClient(withInterceptors([authInterceptor]))
     ```
     La interfaz seguirá mostrando un mensaje genérico en 401/403, como ya hace `guidanceFor`.
  3. **Decisión pendiente:** confirmar con producto P-7: ¿vista del pagador o rol de comercio? Hasta entonces, no declarar cumplida la mitad "comercio" de la historia.
- **Comprobación reproducible (PROPUESTO, NO EJECUTADO):**
  ```bash
  # Requiere dos identidades A y B que el mock admita (H03_TOKEN_A / H03_TOKEN_B).
  PID=$(curl -s -X POST "$H03_W2_BASE_URL/payments" \
    -H "Authorization: Bearer $H03_TOKEN_A" -H "Idempotency-Key: $(uuidgen)" \
    -H 'Content-Type: application/json' \
    -d '{"qrId":"<qrId fijo>","amount":<importe del QR>,"currency":"<moneda>"}' | jq -r .paymentId)

  curl -i "$H03_W2_BASE_URL/payments/$PID"         -H "Authorization: Bearer $H03_TOKEN_B"  # esperado: 404/403, sin datos del pago
  curl -i "$H03_W2_BASE_URL/payments/$PID/receipt" -H "Authorization: Bearer $H03_TOKEN_B"  # esperado: 404/403, sin datos del recibo
  curl -i "$H03_W2_BASE_URL/payments/$PID"                                                  # esperado: 401 (o documentar que el mock es público)
  ```
  - **Resultado esperado:** B no recibe ningún dato de A.
  - **Si el mock no tiene identidades:** el hallazgo **queda abierto**. Se registra como limitación ("la autorización no se puede verificar con este mock") y no como aprobado.
  - Se añadiría a `test_h03_mock_contract.py` como `MOCK-16` (otra identidad) y `MOCK-17` (sin credenciales).

---

### H-02 · El cliente decide importe y moneda del pago, también en QR de importe fijo (condicional a P-1, P-4)

- **Estado:** DETECTADO (riesgo). No está demostrado que el servidor lo neutralice.
- **Archivo y ubicación:** `src/app/qr-pagos/qr-pago.component.ts` → `amountToPay` (computed) y `confirm()`, que envía `{ qrId, amount, currency }`. Además `qr-pagos.models.ts` → `PaymentRequest`.
- **Evidencia:**
  - `confirm()` construye `{ qrId: qr.qrId, amount, currency: qr.currency }`. `amount` y `currency` salen del estado del navegador.
  - Para `fixed`, `amountToPay` toma `qr.amount`. Un cliente modificado (consola, proxy, otro cliente HTTP) puede enviar otro importe o moneda con el mismo `qrId`.
  - Para `open`, solo se valida `Number.isFinite(v) && v > 0`. Valores como `1e21`, `0.0000001` o más decimales de los que admite la moneda pasan. `step="any"` en la plantilla lo permite.
  - `frontend_spec.md` §12: el importe de la pantalla de resultado "se toma de lo enviado", no de la respuesta de W2.
  - **Brecha de pruebas:** `MOCK-11` solo prueba importe ≤ 0 en monto abierto. No hay prueba de importe distinto al del QR fijo ni de moneda alterada.
  - Reproducir: `grep -n "amountToPay\|currency" src/app/qr-pagos/qr-pago.component.ts`
- **Impacto:** si W2 acepta el importe del cliente en un QR de importe fijo, se puede pagar menos de lo cobrado (manipulación de precio) o en otra moneda. Si no impone máximos ni precisión, aparecen importes absurdos o con pérdida de precisión por coma flotante (P-4: unidad desconocida).
- **Corrección propuesta (PROPUESTO):**
  1. **Servidor (W2):** para QR fijo, derivar importe y moneda del `qrId` y rechazar cualquier discrepancia con `409 QR_CONFLICT`. Para monto abierto, imponer mínimo, máximo y precisión por moneda.
  2. **Cliente (defensa adicional, no sustituye al servidor):**
     - Fijar la representación del importe según P-4. Lo más seguro es enteros en unidad menor.
     - Rechazar notación exponencial y exceso de decimales.
     - Aplicar un tope máximo acordado.
     - Mostrar en el resultado los datos de la respuesta de W2 cuando existan, y no solo lo enviado.
  3. Mantener la regla ya implementada de no confirmar con datos previos ante `QR_CONFLICT`.
- **Comprobación reproducible (PROPUESTO, NO EJECUTADO):**
  ```python
  # api/tests/test_h03_mock_contract.py — PROPUESTO como MOCK-16b
  def test_mock_16b_importe_o_moneda_distintos_al_qr_fijo_son_rechazados(w3, w2):
      qr = _resolved(w3, "H03_QR_PAYLOAD_FIXED")
      for amount, currency in ((qr["amount"] + 1, qr["currency"]),
                               (qr["amount"] * 2, qr["currency"]),
                               (qr["amount"], "XXX")):
          resp = _pay(w2, qr["qrId"], amount, currency, str(uuid.uuid4()))
          assert resp.status_code in (409, 422), resp.text   # si es 200/201 → el hallazgo se confirma
  ```
  - **Resultado esperado:** 409/422 en los tres casos. Un 200/201 confirma el hallazgo.
  - Spec Angular propuesta (`FE-PAGO-20`): con monto abierto, `1e21`, `0.0000001` y el valor `Infinity` dejan `canConfirm()` en `false`. Solo se aplicaría una vez resuelto P-4.

---

### H-03 · La clave de idempotencia solo vive en memoria: riesgo de cobro duplicado

- **Estado:** DETECTADO.
- **Archivo y ubicación:** `src/app/qr-pagos/qr-pago.component.ts`:
  - propiedad `private attempt: Attempt | null`;
  - `resolve()`, que ejecuta `this.attempt = null`;
  - `resetFlow()`, que ejecuta `this.attempt = null`, llamado desde `onFileSelected()`;
  - `confirm()`.
  Además `qr-api.service.ts` → `newIdempotencyKey()`.
- **Evidencia:**
  - La clave se guarda solo en el campo `attempt` del componente. Se pierde al recargar o cerrar la pestaña.
  - `onFileSelected()` → `resetFlow()` y `resolve()` ponen `attempt = null`. Tras un fallo de red o un 5xx (resultado ambiguo: W2 pudo haber cobrado), si la persona vuelve a elegir **el mismo QR con el mismo importe**, el siguiente `confirm()` genera una clave nueva.
  - `FE-PAGO-09` solo prueba la reutilización dentro de la misma instancia del componente.
  - Reproducir: `grep -n "attempt" src/app/qr-pagos/qr-pago.component.ts`
  - Secundario: en `newIdempotencyKey()`, si `globalThis.crypto` no existe, `c?.randomUUID` es falso y luego se ejecuta `c.getRandomValues(...)` sobre `undefined`, que lanza `TypeError` dentro de `confirm()`. Es un fallo de disponibilidad, no una debilidad criptográfica.
- **Impacto:** cobro duplicado al dinero de la persona tras un resultado ambiguo. Lo agravan los reintentos manuales, que son justo lo que la guía de recuperación sugiere. Es una pérdida de integridad financiera, no de confidencialidad.
- **Corrección propuesta (PROPUESTO):**
  ```typescript
  // Esbozo. Almacenamiento de sesión, solo para el intento pendiente.
  const PENDING_KEY = 'merchantQrPayments.pending';
  // Al crear el intento: sessionStorage.setItem(PENDING_KEY,
  //   JSON.stringify({ fp: `${qr.qrId}|${amount}|${qr.currency}`, key, at: Date.now() }));
  // Al preparar confirm(): reutilizar la clave si 'fp' coincide y 'at' < 24 h.
  // Borrar la entrada solo ante éxito, QR_EXPIRED, QR_CONFLICT o IDEMPOTENCY_CONFLICT.
  // Quitar 'this.attempt = null' de resolve()/resetFlow() cuando el fingerprint coincide.
  ```
  - Tras un resultado ambiguo (red caída o 5xx), mostrar un aviso: "Antes de reintentar, revisa el historial o consulta la referencia".
  - Respaldo en `newIdempotencyKey()`: si no hay `crypto`, bloquear el pago con un mensaje en lugar de lanzar.
- **Comprobación reproducible (PROPUESTO, NO EJECUTADO):**
  Spec `FE-PAGO-20`:
  1. Cargar QR → confirmar → `req.error(new ProgressEvent('error'))`. Anotar el `Idempotency-Key`.
  2. Destruir y recrear el componente, o volver a llamar a `onFileSelected()` con el mismo QR y el mismo importe.
  3. Confirmar de nuevo.
  4. **Esperado:** el mismo `Idempotency-Key`. Hoy se espera una clave distinta, y eso confirma el hallazgo.

  Manual (E2E, mock apagado): confirmar, apagar el mock, recargar la página, encender el mock, cargar el mismo QR y confirmar. Debe llegar la misma clave al mock.

---

### H-04 · El recibo se muestra tal cual, sin lista de campos permitidos

- **Estado:** DETECTADO.
- **Archivos y ubicación:** `src/app/qr-pagos/historial.component.ts` → `viewReceipt()`; plantilla `historial.component.html` → bloque `@if (receipt(); as r)`. También `qr-api.service.ts` → `getReceipt()`, que devuelve el objeto completo.
- **Evidencia:**
  - `viewReceipt` recorre `Object.entries(r)` y pinta **cada** campo: `JSON.stringify(v)` para objetos y `String(v)` para el resto.
  - `frontend_spec.md` §2: "se muestra tal cual, campo a campo".
  - `getReceipt` solo valida que sea un objeto.
  - Reproducir: `grep -n "Object.entries\|JSON.stringify" src/app/qr-pagos/historial.component.ts`
- **Impacto:** cualquier campo que W2 añada al recibo (documento del pagador, identificadores internos, cuentas, datos de otros pagos) se muestra sin revisión. Es exposición de datos sensibles por diseño y no se puede acotar sin conocer el contrato (P-1). Nótese que escapar el HTML (Angular lo hace) no protege la **confidencialidad**.
- **Corrección propuesta (PROPUESTO):** lista de campos permitidos, con etiquetas fijas y valores formateados como texto. Los nombres son ilustrativos hasta definir P-1.
  ```typescript
  const RECEIPT_FIELDS: ReadonlyArray<[key: string, label: string]> = [
    ['reference', 'Referencia'], ['status', 'Estado'],
    ['amount', 'Importe'], ['currency', 'Moneda'], ['merchantName', 'Comercio'],
  ];
  // Mostrar solo esas claves; ignorar el resto y no serializar objetos anidados.
  ```
  Registrar en `design.md` qué campos del recibo se consideran públicos para quien lo consulta.
- **Comprobación reproducible (PROPUESTO, NO EJECUTADO):**
  Spec `FE-HIST-10`: `flush({ reference:'REF-1', status:'ok', payerDocument:'123', internalId:'x', nested:{a:1} })`. **Esperado:** `receipt().fields` contiene solo `reference` y `status`; el texto renderizado no contiene `123`, `internalId` ni `nested`. Hoy `FE-HIST-08` espera que se muestren todos los campos, por lo que hay que reemplazarlo cuando se implemente la corrección.

---

### H-05 · Historial local en claro, sin identidad, sin borrado y sin CSP definida

- **Estado:** DETECTADO.
- **Archivo y ubicación:** `src/app/qr-pagos/payment-history.service.ts` → constantes `STORAGE_KEY`, `write()`, `read()`. Además la ausencia de una acción de borrado en `historial.component.html`.
- **Evidencia:**
  - Se guarda en `localStorage` (clave `merchantQrPayments.history`) `paymentId`, `reference`, `status`, `qrId`, `merchantName`, `amount`, `currency` y fecha, sin cifrado y sin asociarlos a ninguna identidad (S-6 del Arquitecto).
  - No existe método de borrado total ni botón en la interfaz. Solo las pruebas lo borran, con `localStorage.removeItem`.
  - Reproducir: `grep -n "localStorage\|STORAGE_KEY" src/app/qr-pagos/payment-history.service.ts`
  - `isEntry()` valida tipos primitivos pero no formato ni longitud. La interfaz usa interpolación de Angular, que escapa, así que no es un XSS por sí mismo.
- **Impacto:**
  - En un dispositivo o perfil compartido, otra persona ve comercios, importes y referencias de pagos ajenos.
  - Cualquier XSS futuro o script de terceros en el mismo origen lee y modifica el historial.
  - El dato manipulado alimenta consultas a W2 (ver H-01 y H-06).
  - La limitación de diseño debe quedar declarada. La historia pide expresamente un historial local, así que la corrección es de mitigación, no de rediseño.
- **Corrección propuesta (PROPUESTO):**
  1. Añadir `clearAll()` en el servicio y un botón "Borrar historial de este navegador" con confirmación.
  2. Cuando exista identidad, asociar la clave a esa identidad (por ejemplo, con un identificador derivado que no exponga el valor original) y vaciarla al cerrar sesión. No inventar la derivación antes de que se defina la identidad.
  3. Aviso breve en `/historial`: "Se guarda en este navegador; usa «Borrar historial» en equipos compartidos."
  4. Servir la aplicación con CSP restrictiva (`default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'`). Es configuración del servidor de la app, fuera de estos archivos.
  5. Almacenar solo los campos estrictamente necesarios.
- **Comprobación reproducible (PROPUESTO, NO EJECUTADO):**
  - Spec `FE-STO-10`: tras `add()`, `clearAll()` deja `localStorage.getItem(KEY) === null` y `entries()` vacío.
  - Manual: `curl -sI <URL de la app> | grep -i content-security-policy`. **Esperado:** cabecera presente con las directivas anteriores. Hoy no hay evidencia de que exista.

---

### H-06 · `paymentId` sin validar de formato y usado como segmento de ruta

- **Estado:** DETECTADO. Impacto bajo y sin explotación demostrada.
- **Archivos y ubicación:**
  - `src/app/qr-pagos/qr-pagos.config.ts` → `w2PaymentStatusPath`, `w2PaymentReceiptPath` (solo `encodeURIComponent`).
  - `src/app/qr-pagos/qr-api.service.ts` → `parsePayment()` (`isText` solo comprueba cadena no vacía).
  - `src/app/qr-pagos/payment-history.service.ts` → `isEntry()`.
- **Evidencia:**
  - `encodeURIComponent('..')` devuelve `'..'`: los puntos no se codifican. El resultado `/payments/..` o `/payments/../receipt` lo normaliza el navegador al resolver la URL, según la normalización estándar de dot-segments. No lo comprobé en este laboratorio.
  - Un `paymentId` con ese valor puede llegar de una respuesta de W2 o de un `localStorage` manipulado.
  - Reproducir: `grep -n "encodeURIComponent" src/app/qr-pagos/qr-pagos.config.ts`
- **Impacto:** una petición GET de lectura puede dirigirse a una ruta distinta de la prevista dentro del origen de W2. Es bajo, porque lo controla W2 o la propia persona.
- **Corrección propuesta (PROPUESTO):**
  ```typescript
  export const SAFE_ID = /^[A-Za-z0-9_-]{1,128}$/;   // ajustar al formato real de P-1
  // Usar en isEntry() y parsePayment(); en w2Payment*Path(): si !SAFE_ID.test(id) → lanzar ApiError(200,'RESPONSE_INVALID',null)
  ```
  Aviso: `FE-SVC-08` hoy espera que `'a/b c'` se codifique y se consulte. Con esta corrección ese caso pasa a ser rechazado, así que la spec debe actualizarse.
- **Comprobación reproducible (PROPUESTO, NO EJECUTADO):** specs nuevas. (a) `localStorage` con `paymentId:'..'` → la entrada se ignora. (b) `createPayment` con respuesta `paymentId:'../x'` → `RESPONSE_INVALID`. (c) `getPayment('..')` → no emite petición. **Esperado:** `http.expectNone(() => true)` en los tres.

---

### H-07 · Dependencias: pines sin verificar, sin hashes y sin revisión del frontend

- **Estado:** DETECTADO (riesgo). **No hay consulta a PyPI/OSV hecha por mí.**
- **Archivo y ubicación:** `api/requirements.txt` (`fastapi==0.115.6`, `starlette==0.41.3`, `pydantic==2.10.3`, `uvicorn==0.32.1`). Además el `package.json` y el lockfile del frontend, que no recibí.
- **Evidencia:**
  - `backend_spec.md` §9 declara que los pines son una propuesta **no verificada** contra PyPI/OSV a 2026-11-06 y que no se ejecutó `pip install` ni `pip check`.
  - Los requisitos no incluyen hashes (`--require-hashes`) ni herramientas de prueba (`pytest`, `httpx`), que quedan sin pin (T-5 del informe de pruebas).
  - Según mi conocimiento, no verificado, existen avisos públicos de Starlette posteriores a la fecha de lanzamiento de estos pines, relacionados con el procesamiento multipart y con `FileResponse`. **No afirmo que estas versiones estén afectadas.** La aplicación no usa multipart ni `FileResponse`, así que la superficie sería baja, pero debe confirmarse con OSV. Como `fastapi 0.115.6` acota `starlette` por rango, cualquier cambio de Starlette implica cambiar FastAPI y probar de nuevo.
  - El Issue no es una actualización de dependencias (S-2).
- **Impacto:** posible vulnerabilidad conocida sin detectar. Sin hashes, la instalación acepta cualquier artefacto que coincida con la versión.
- **Corrección propuesta (PROPUESTO):**
  - Consultar OSV/PyPI por cada pin y registrar fecha, fuente y resultado. Es el procedimiento §8.5 del informe de pruebas, que sigue sin ejecutar.
  - Si hay avisos aplicables, proponer versiones exactas **con esa consulta como fuente**. No fijo versiones concretas sin ella.
  - Generar el lockfile con hashes y mover `pytest`/`httpx` a un `requirements-dev.txt` con pin.
  - Aprobar con versión exacta fijada cualquier librería de decodificación QR futura (P-3).
- **Comprobación reproducible (PROPUESTO, NO EJECUTADO):**
  ```bash
  cd api && python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt && pip check
  pip install pip-audit && pip-audit -r requirements.txt            # fuente: base OSV/PyPI, anotar fecha
  for p in "fastapi 0.115.6" "starlette 0.41.3" "pydantic 2.10.3" "uvicorn 0.32.1"; do
    set -- $p; curl -s https://api.osv.dev/v1/query \
      -d "{\"package\":{\"name\":\"$1\",\"ecosystem\":\"PyPI\"},\"version\":\"$2\"}" | tee "evidencia/C2_osv_$1.json"
  done
  # Frontend, con los comandos reales del repo (P-2):
  npm ci && npm audit --omit=dev
  ```
  **Esperado:** 0 avisos aplicables, o cada aviso registrado con su decisión.

---

### H-08 · Manejador de errores del backend: reflejo de `detail`, nombres de campo y log sin sanear

- **Estado:** DETECTADO. Sin endpoints de negocio hoy, así que el impacto es bajo.
- **Archivo y ubicación:** `api/app/errors.py`:
  - `http_exception_handler` (rama `status not in _MESSAGES`);
  - `validation_exception_handler`;
  - `unhandled_exception_handler`.
- **Evidencia:**
  - En `http_exception_handler`, para un 4xx que no esté en `_MESSAGES` (por ejemplo, 418, 429 o 415) se devuelve `exc.detail` tal cual. El propio `ERR-01` lo fija como esperado: `(418, "soy-tetera", "HTTP_ERROR", "soy-tetera")`. Un `detail` escrito con datos internos por un futuro desarrollador llegaría al cliente.
  - En `validation_exception_handler`, los nombres de campo salen de `err["loc"]`. Con modelos `extra="forbid"` o con cuerpos de tipo diccionario, esas posiciones incluyen **claves que envía el cliente**, que se reflejan en `message` sin límite de longitud. Es JSON, no HTML, así que no hay XSS. Es reflejo de datos controlados por el cliente.
  - En `unhandled_exception_handler`, `logger.exception("... %s %s", request.method, request.url.path)` registra la ruta decodificada. Un `%0A` en la URL puede insertar saltos de línea (falsificación de líneas de log). Es probable, **no verificado**.
  - Reproducir: `grep -n "exc.detail\|request.url.path\|loc" api/app/errors.py`
- **Impacto:** fuga puntual de información de depuración, contenido controlado por el cliente reflejado y ruido o falsificación en los logs.
- **Corrección propuesta (PROPUESTO):**
  ```python
  # 1) Mensaje genérico para todo 4xx no mapeado
  message = _MESSAGES.get(status, "Error en la solicitud." if status < 500 else "Error interno del servidor.")
  # 2) Nombres de campo: solo caracteres seguros y longitud acotada
  import re
  _SAFE = re.compile(r"[^\w.\[\]-]")
  fields = sorted({_SAFE.sub("?", ".".join(map(str, e.get("loc", ())))[:64]) for e in exc.errors()})
  # 3) Log con la ruta escapada
  logger.exception("Error no controlado en %s %s", request.method, ascii(request.url.path))
  ```
  `ERR-01` para 418 deberá cambiar su esperado a `"Error en la solicitud."`. Declararlo en el commit.
- **Comprobación reproducible (PROPUESTO, NO EJECUTADO):**
  ```python
  # en test_h03_error_format.py (app local con una ruta /boom/{x} que lanza RuntimeError)
  def test_err_07_el_log_no_contiene_saltos_de_linea_de_la_ruta(client, caplog):
      with caplog.at_level(logging.ERROR, logger="app.errors"):
          client.get("/boom/a%0AERROR%20falso")
      assert all("\n" not in r.getMessage() for r in caplog.records)
  ```
  Y para el reflejo: un modelo `extra="forbid"` con `POST {"x"*500: 1}` → `message` de longitud ≤ 120 y sin la clave completa.

---

### H-09 · OpenAPI y documentación expuestas por defecto; `LOG_LEVEL` sin validar

- **Estado:** DETECTADO.
- **Archivos y ubicación:** `api/app/main.py` → `FastAPI(title=..., version=...)`. `api/app/config.py` → `LOG_LEVEL`. `main.py` → `logging.basicConfig(level=config.LOG_LEVEL)`.
- **Evidencia:**
  - `FastAPI(...)` sin `docs_url`, `redoc_url` ni `openapi_url`: `/docs`, `/redoc` y `/openapi.json` quedan públicos. `API-07` y `PER-02` de los tests dependen de que `/openapi.json` exista.
  - `LOG_LEVEL` sale de `os.getenv(...).upper()` y llega a `logging.basicConfig`. Un valor inválido lanza `ValueError` al importar el módulo y el servicio no arranca.
  - Reproducir: `grep -n "FastAPI(\|basicConfig\|LOG_LEVEL" api/app/main.py api/app/config.py`
- **Impacto:** divulgación del contrato interno en producción (bajo hoy, solo `/health`) e indisponibilidad por mala configuración.
- **Corrección propuesta (PROPUESTO):**
  ```python
  # config.py
  ENABLE_DOCS: bool = os.getenv("ENABLE_DOCS", "false").lower() == "true"
  _LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
  LOG_LEVEL = LOG_LEVEL if LOG_LEVEL in _LEVELS else "INFO"
  # main.py
  app = FastAPI(title=config.SERVICE_NAME, version=config.API_VERSION,
                docs_url="/docs" if config.ENABLE_DOCS else None,
                redoc_url=None, openapi_url="/openapi.json" if config.ENABLE_DOCS else None)
  ```
  Las pruebas `API-07` y `PER-02` deben fijar `ENABLE_DOCS=true` con `monkeypatch`. Esto debe hacerse antes de importar la app, o recargar el módulo. Declarar el cambio de pruebas.
- **Comprobación reproducible (PROPUESTO, NO EJECUTADO):**
  ```bash
  cd api && uvicorn app.main:app &
  curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/openapi.json   # esperado 404 por defecto
  curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/docs            # esperado 404
  LOG_LEVEL=basura python -c "import app.main"                                    # esperado: arranca (INFO), sin ValueError
  ```

---

### H-10 · Sin límite de tamaño de archivo ni de payload en el cliente (P-6)

- **Estado:** DETECTADO.
- **Archivos y ubicación:** `src/app/qr-pagos/qr-decoder.service.ts` → `decode()` (`createImageBitmap(file)`); `qr-api.service.ts` → `resolve()` (no limita `payload`).
- **Evidencia:** `decode()` solo comprueba `file.type.startsWith('image/')`, que depende del navegador y de la extensión, y decodifica cualquier tamaño. El `payload` obtenido del QR se envía sin límite. `frontend_spec.md` §5: "el frontend no impone uno" (P-6 abierto).
  Reproducir: `grep -n "file.size\|maxLength\|payload.length" src/app/qr-pagos/*.ts` (sin coincidencias esperadas).
- **Impacto:** imágenes enormes bloquean o agotan memoria de la pestaña. Un payload gigante se envía a W3. Es autoinfligido, así que bajo.
- **Corrección propuesta (PROPUESTO):**
  - Rechazar archivos mayores que un tope acordado (provisional: 5 MB, a confirmar).
  - Rechazar un payload decodificado con más caracteres que el límite de P-6, antes de enviarlo.
  - Ambos casos con una razón nueva en `QrDecodeError` y mensaje local, sin llamada de red.
- **Comprobación reproducible (PROPUESTO, NO EJECUTADO):** spec `FE-DEC-07`: un `File` de 6 MB con `type: 'image/png'` rechazado sin invocar al motor. Spec `FE-PAGO-21`: motor que devuelve un texto de límite+1 caracteres → `http.expectNone('/qrs/resolve')`.

---

### H-11 · Orígenes, CORS, CSP y credenciales sin definir (informativo)

- **Estado:** DETECTADO (informativo).
- **Archivos y ubicación:** `src/app/qr-pagos/qr-pagos.config.ts` → tokens `W2_BASE_URL` y `W3_BASE_URL` (`factory: () => ''`). `api/app/main.py` → sin `CORSMiddleware`.
- **Evidencia:** las URL base se pueden sobrescribir por DI sin lista permitida. No hay política CORS ni CSP descrita. No se usa `withCredentials`.
- **Impacto:** si la URL base llegara de una configuración editable por terceros, los pagos podrían dirigirse a un origen no previsto. Si alguien "arregla" un error de CORS con `allow_origins=["*"]` más credenciales, se abre una superficie de CSRF.
- **Corrección propuesta (PROPUESTO):**
  - Definir las bases solo en el entorno de compilación.
  - Si se necesita CORS, usar una lista explícita de orígenes y no `*` con credenciales.
  - Si W2 usa cookies, exigir protección CSRF (la protección XSRF de Angular solo cubre solicitudes con URL relativa).
- **Comprobación reproducible (PROPUESTO, NO EJECUTADO):**
  ```bash
  curl -si -X OPTIONS http://127.0.0.1:8000/health -H 'Origin: https://evil.example' \
    -H 'Access-Control-Request-Method: GET' | grep -i access-control   # esperado: sin cabeceras CORS permisivas
  ```

---

## 3. Mapa de comprobaciones

| Hallazgo | Comprobación | Tipo | Estado |
|---|---|---|---|
| H-01 | `curl` con dos identidades; `MOCK-16`/`MOCK-17` | Manual + pytest propuesto | NO EJECUTADO |
| H-02 | `MOCK-16b`; `FE-PAGO-20` | pytest + Angular propuestos | NO EJECUTADO |
| H-03 | `FE-PAGO-20` (reutilización tras recarga); E2E con mock apagado | Angular + manual propuestos | NO EJECUTADO |
| H-04 | `FE-HIST-10` | Angular propuesto | NO EJECUTADO |
| H-05 | `FE-STO-10`; `curl -sI` para CSP | Angular + manual propuestos | NO EJECUTADO |
| H-06 | specs de `SAFE_ID` | Angular propuestas | NO EJECUTADO |
| H-07 | `pip-audit`, consultas OSV, `npm audit` | Manual propuesto | NO EJECUTADO |
| H-08 | `ERR-07` y reflejo de nombres de campo | pytest propuesto | NO EJECUTADO |
| H-09 | `curl` a `/openapi.json`, `LOG_LEVEL=basura` | Manual propuesto | NO EJECUTADO |
| H-10 | `FE-DEC-07`, `FE-PAGO-21` | Angular propuestas | NO EJECUTADO |
| H-11 | `OPTIONS` con `Origin` ajeno | Manual propuesto | NO EJECUTADO |

Procedimiento común para todo hallazgo corregido:
1. Ejecutar primero la comprobación **antes** de aplicar la corrección y conservar la salida (debe reproducir el hallazgo).
2. Aplicar la corrección.
3. Ejecutar de nuevo y conservar la salida (debe pasar).
4. Ejecutar la suite completa (`python tools/lab.py test api` y los comandos del frontend de P-2) para descartar regresiones.

Guardar las salidas en `evidencia/` con `tee`, con fecha, hora y hash del commit. Un `skip` cuenta como **no cumplido**.

---

## 4. Controles revisados sin hallazgo (por lectura, no ejecutados)

| Área | Observación | Cómo comprobarlo |
|---|---|---|
| Inyección SQL | No hay base de datos ni SQL en el cambio (backend §7). No hay superficie. | `grep -rniE "select |insert |execute\(" api/app src/app/qr-pagos` → sin coincidencias esperadas. |
| Inyección de comandos | `subprocess.run` solo aparece en pruebas, con argumentos fijos (`API-08`/`API-09`). | `grep -rn "subprocess\|os.system\|eval(" api src` |
| XSS | Las plantillas usan interpolación de Angular. No vi `innerHTML`, `bypassSecurityTrust*` ni `[innerHTML]`. `merchant.name` y `serviceMessage` se interpolan como texto. | `grep -rnE "innerHTML|bypassSecurityTrust" src/` y `FE-PAGO-18` (propuesta del probador, no ejecutada). |
| Imagen QR | Solo viaja `{payload}` a W3. La imagen se procesa en el navegador. | `FE-SVC-01`, `FE-PAGO-01`, `E2E-01` (no ejecutados). |
| Secretos | No hay credenciales, claves ni tokens en los archivos entregados. Los sentinelas (`clave-secreta-123`, `password=abc`) son datos de prueba. Las variables `H03_*` son URL y payloads del mock, no secretos. | `grep -rniE "secret|token|apikey|password" api src` y revisar que `.env*` no esté versionado. |
| Fuga en 422/500 | El 422 lista solo nombres de campo y el 500 es genérico con traza en el log (ver H-08 para los matices). | `ERR-03` a `ERR-06` (no ejecutados). |
| Doble envío | `confirm()` pasa a `submitting` de forma síncrona antes de la petición. | `FE-PAGO-08` (no ejecutado). |
| Subidas en servidor | No hay `multipart`; el backend no escribe en disco. | `PER-01`, `PER-02` (no ejecutados). |

Si el mock exige credenciales (P-8), no deben guardarse en `localStorage` ni en archivos versionados. Deben llegar por variables de entorno o un almacén de secretos.

---

## 5. Registro de verificaciones

| Verificación | Realizada | Resultado | Evidencia |
|---|---|---|---|
| Revisión estática manual de los artefactos entregados | **Sí (lectura)** | 11 hallazgos y controles sin hallazgo de §4 | Este informe, con los `grep` indicados |
| `python tools/lab.py test api` | No | **NO EJECUTADO** | — |
| `pytest` H03 (API y mock) | No | **NO EJECUTADO** | — |
| Specs Angular `FE-*` | No | **NO EJECUTADO** | — |
| Build, verificación del repo (P-2) | No | **NO EJECUTADO** | — |
| E2E-01 … E2E-09 | No | **NO EJECUTADO** | — |
| `pip install`, `pip check`, `pip-audit`, consultas OSV/PyPI | No | **NO EJECUTADO** | — |
| `npm audit` | No | **NO EJECUTADO** | — |
| Comprobaciones H-01 … H-11 de este informe | No | **NO EJECUTADO** | — |
| Aplicación de las correcciones propuestas | No | **NO APLICADAS** | — |

Ninguna corrección está aplicada y ninguna se probó. Hasta que se ejecute lo anterior, **no se puede declarar cumplido** el criterio CA-7 ni cerrar ningún hallazgo.

---

## 6. Preguntas abiertas que condicionan la severidad

| Pregunta | Afecta a |
|---|---|
| P-1: contrato real de W2/W3 (campos, rutas, cabecera de idempotencia, códigos) | H-01, H-02, H-04, H-06 |
| P-4: unidad y moneda del importe, y límites máximos | H-02 |
| P-6: límite de tamaño del payload | H-10 |
| P-7: ¿existe un rol de comercio dentro de la aplicación o la vista es solo del pagador? | H-01 |
| P-8: ¿el mock exige credenciales y existen varias identidades para probar acceso cruzado? | H-01, H-11 |
| P-3: ¿qué librería de decodificación QR se aprueba, con versión exacta? | H-07, H-10 |
| P-2: comandos oficiales de build, verificación y E2E | todas las comprobaciones |

---

## 7. Orden de corrección sugerido

1. **H-01 y H-02:** son decisiones de servidor y de contrato. Resolver P-1, P-7 y P-8 y añadir `MOCK-16`, `MOCK-16b` y `MOCK-17`, que pueden fallar y esa falla sería informativa.
2. **H-03:** persistencia del intento de pago en `sessionStorage` y aviso tras resultado ambiguo.
3. **H-04 y H-05:** lista de campos permitidos del recibo y borrado del historial más CSP.
4. **H-06, H-08, H-09, H-10:** endurecimientos pequeños y localizados (cada uno con su spec o test propuesto).
5. **H-07 y H-11:** consulta OSV/PyPI, hashes y revisión de orígenes. Documentar la decisión.

Al aplicar cada corrección, actualizar las pruebas existentes que fijan el comportamiento actual (`ERR-01` para 418, `FE-SVC-08`, `FE-HIST-08`, `API-07` y `PER-02`). Declararlo explícitamente en el cambio.