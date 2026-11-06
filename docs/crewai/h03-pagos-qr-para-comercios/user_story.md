# user_story.md

## Historia de usuario H03: Pagos QR para comercios

**Como** persona que paga en un comercio,
**quiero** cargar una imagen QR, ver el comercio y el importe validados y confirmar el pago por el flujo W2 existente,
**para** pagar sin errores de importe o de comercio.

**Como** comercio,
**quiero** consultar referencia, estado y recibo de los pagos QR iniciados desde la aplicación,
**para** conciliar los cobros hechos por este flujo.

> Nota de lectura: las secciones separan **[Explícito]** (dicho en el Issue), **[Supuesto]** (decisión conservadora mía, a confirmar) y **[Pregunta]** (dato faltante). El Issue cita los archivos OpenSpec (`proposal.md`, `design.md`, `spec.md`, `tasks.md`) y las interfaces W2/W3, pero no se incluyó su contenido en el contexto. Por eso no puedo confirmar los contratos exactos de W2 ni de W3.

---

## 1. Resumen del cambio y alcance

### 1.1 Resumen [Explícito]
- El navegador decodifica la imagen QR y envía **solo el payload textual** a W3 `POST /qrs/resolve`.
- La aplicación muestra comercio e importe antes de confirmar. Para QR de monto abierto exige un importe positivo.
- El pago se crea con W2 `POST /payments`, preservando `qrId` y la idempotencia.
- El estado y los recibos se consultan en W2. Los eventos del mock se entregan manualmente y no son webhooks automáticos.
- El historial se muestra y se filtra localmente, solo para pagos iniciados por este flujo. La fecha se etiqueta como fecha local registrada.
- Se guía la recuperación ante QR inválido, desconocido, expirado o con conflicto de comercio/importe.
- Se completa compilación, verificación del repositorio y pruebas end-to-end con el mock configurado, registrando resultados reales y limitaciones.

### 1.2 Dentro del alcance
- Frontend Angular: decodificación, resolución, confirmación, consulta de estado/recibo, historial local y mensajes de recuperación.
- Pruebas unitarias y end-to-end contra el mock configurado.

### 1.3 Fuera del alcance [Explícito]
- Modificar la API mock, que es de solo lectura.
- Generar QR.
- Escanear con cámara.
- Tratar los eventos del mock como webhooks automáticos.

### 1.4 Decisiones de alcance [Supuesto]
- **S-1.** El Issue no pide endpoints nuevos ni persistencia en servidor. La capa FastAPI (`api/app/`) **no cambia** en esta historia. W2 y W3 son servicios externos (mock) que la aplicación consume.
- **S-2.** No se actualizan dependencias, porque el Issue no lo pide. No hay pins de `requirements*.txt` ni de `starlette` que definir. Si se añade una librería de decodificación QR al frontend, requiere aprobación explícita y versión exacta en el lockfile del frontend (ver P-3).
- **S-3.** Los seis issues hijos cubren las tareas 1 a 6 del OpenSpec. Esta historia es el paraguas y su criterio 7 es la verificación transversal.

---

## 2. Componentes afectados, responsabilidades y límites

Las rutas del frontend no se conocen. Los nombres son lógicos y las rutas exactas se fijan según la estructura existente del repositorio (P-2).

| # | Componente | Responsabilidad | Límite (lo que NO hace) |
|---|---|---|---|
| C1 | **Decodificador QR (navegador)** | Leer la imagen, extraer el payload textual y devolver texto o error de decodificación. | No envía la imagen ni datos binarios a ningún servicio. No usa cámara. |
| C2 | **Cliente W3 `qrs/resolve`** | Hacer `POST /qrs/resolve` con solo el payload textual. Normalizar respuesta y errores. | No interpreta el payload localmente para decidir comercio o importe. |
| C3 | **Pantalla de revisión y confirmación** | Mostrar comercio e importe resueltos antes de confirmar. Para monto abierto, exigir importe > 0 y bloquear la confirmación si no se cumple. | No crea el pago sin confirmación explícita. |
| C4 | **Cliente W2 `payments`** | Hacer `POST /payments` preservando `qrId` e idempotencia. Consultar estado y recibo. | No simula webhooks. No reinterpreta estados del mock. |
| C5 | **Historial local** | Guardar en el navegador solo los pagos iniciados por este flujo. Listar y filtrar localmente. Etiquetar la fecha como "fecha local registrada". | No lista pagos de otros flujos ni consulta un listado remoto. |
| C6 | **Guía de recuperación** | Mapear errores a mensajes y acciones: QR inválido, desconocido, expirado, conflicto de comercio/importe. | No reintenta automáticamente un `POST /payments` ante conflicto. |
| C7 | **Verificación (build, repo, E2E)** | Compilar, ejecutar las verificaciones del repositorio y los E2E con el mock configurado. Registrar resultados reales y limitaciones. | No modifica el mock. |
| C8 | **Capa FastAPI (`api/app/`)** | Sin cambios (S-1). | No se añaden `main.py`, `routers/`, `services.py`, `schemas.py` ni `config.py` nuevos para H03. |

### 2.1 Persistencia local: riesgos y decisiones [Supuesto]
- **Concurrencia (mismo usuario, varias pestañas):**
  - Cada escritura hace leer-modificar-escribir sobre el almacenamiento local y deduplica por clave de idempotencia o `paymentId`.
  - Se escucha el evento `storage` para refrescar la lista.
  - Resultado esperado: dos pestañas no duplican ni pisan entradas.
- **Datos preexistentes:**
  - El historial se guarda bajo una clave con versión de esquema (por ejemplo, `schemaVersion: 1`).
  - Entradas con formato desconocido o corrupto se ignoran sin romper la pantalla.
  - No se borran datos ajenos al flujo.
- **Migración:** no aplica en la primera versión, porque se crea `schemaVersion: 1`. Si ya existe una clave con otra forma, se declara en P-5 antes de implementar.
- **Identidad:**
  - El Issue no define identidad de usuario.
  - No se deriva ni se expone ningún valor del propietario, y no se usa hash SHA-256 ni directorio por propietario.
  - Si una historia futura añade persistencia en servidor, se aplicaría esta regla: la identidad sale de una dependencia de FastAPI (nunca del cliente), el directorio del propietario se deriva con SHA-256 y ningún valor derivado aparece en las respuestas.

---

## 3. Contrato de API relevante

### 3.1 Estado de la información
El Issue fija solo los endpoints (`W3 POST /qrs/resolve`, `W2 POST /payments`) y que existen consultas de estado y recibo en W2. **No se proporcionó** el esquema de ninguno de estos endpoints: nombres de campos, cabecera de idempotencia, rutas de consulta de estado y recibo, ni formato de errores del mock. Lo siguiente es un **contrato de trabajo supuesto**, que debe validarse contra `design.md`, `spec.md` y el mock configurado antes de implementar (P-1).

### 3.2 W3 `POST /qrs/resolve`

**Entrada [Explícito + Supuesto]**
- Solo el payload textual del QR. El nombre del campo es [Supuesto]: `payload`.
- No se envía imagen.

```json
{ "payload": "<texto decodificado del QR>" }
```

**Respuesta exitosa [Supuesto: campos mínimos que la UI necesita]**
```json
{
  "qrId": "qr_123",
  "merchant": { "name": "Comercio Ejemplo" },
  "amountType": "fixed",
  "amount": 12500,
  "currency": "COP"
}
```
- Para monto abierto, `amountType: "open"` y `amount` ausente o nulo.
- Moneda y unidad del importe: P-4.

**Errores [Supuesto]**: cuerpo único `{"code","message"}`.

| Situación | HTTP | `code` | Acción de la UI |
|---|---|---|---|
| Payload no decodificable o formato inválido | 400 | `QR_INVALID` | Pedir otra imagen. |
| QR no reconocido | 404 | `QR_UNKNOWN` | Informar que el QR no pertenece a un comercio conocido. |
| QR expirado | 410 | `QR_EXPIRED` | Pedir un QR vigente al comercio. |
| Conflicto de comercio/importe | 409 | `QR_CONFLICT` | Volver a resolver el QR y no confirmar con datos previos. |
| Payload demasiado grande | 413 | `PAYLOAD_TOO_LARGE` | Rechazar antes o después del envío y pedir otro QR. El límite es P-6. |
| Sin identidad o autorización (si el mock la exige) | 401 | `UNAUTHORIZED` | Mensaje genérico. Solo si el mock lo devuelve. |

### 3.3 W2 `POST /payments`

**Entrada [Supuesto]**
```json
{ "qrId": "qr_123", "amount": 12500, "currency": "COP" }
```
- `qrId` se preserva tal como lo devolvió W3.
- Idempotencia: una clave única por intento de confirmación, enviada en el mecanismo que defina W2 (por ejemplo, cabecera `Idempotency-Key`, a confirmar en P-1).
- Un reintento del mismo intento reutiliza la misma clave. Un intento nuevo, con otro importe o QR, genera una clave nueva.
- Para monto abierto, `amount` es obligatorio y > 0. La UI lo valida antes de enviar.

**Respuesta exitosa [Supuesto]**
```json
{
  "paymentId": "pay_456",
  "reference": "REF-0001",
  "status": "pending",
  "qrId": "qr_123"
}
```

**Errores [Supuesto]**: mismo cuerpo `{"code","message"}`.

| Situación | HTTP | `code` |
|---|---|---|
| Importe ausente o no positivo | 422 | `AMOUNT_INVALID` |
| QR expirado | 410 | `QR_EXPIRED` |
| Conflicto de comercio/importe | 409 | `QR_CONFLICT` |
| Reutilización de clave de idempotencia con cuerpo distinto | 409 | `IDEMPOTENCY_CONFLICT` |
| Sin identidad | 401 | `UNAUTHORIZED` |

### 3.4 W2: consulta de estado y recibo
- Rutas y esquemas: **no determinables con la información disponible** (P-1).
- Regla explícita: los eventos del mock se entregan manualmente. La UI ofrece una acción "Actualizar estado" y no hace polling que simule webhooks. Esto es [Supuesto] derivado del criterio 4 y debe validarse en `design.md`.

### 3.5 Información faltante
- Esquemas reales de W2 y W3.
- Cabecera o campo de idempotencia.
- Códigos HTTP y `code` reales del mock.
- Rutas de estado y recibo.
- Si el mock requiere credenciales.

Todo esto está en la sección 5.

---

## 4. Trazabilidad de criterios de aceptación

| # | Criterio | Componente | Verificación |
|---|---|---|---|
| CA-1 | Decodificar imágenes QR en el navegador y enviar solo el payload textual a W3 `POST /qrs/resolve`. | C1, C2 | **Unit:** con una imagen QR de prueba, C1 devuelve el texto esperado. **Unit:** el cuerpo enviado por C2 contiene solo el payload. **E2E:** al cargar la imagen, la petición capturada a `/qrs/resolve` no incluye datos de imagen. |
| CA-2 | Mostrar comercio e importe antes de confirmar; exigir importe positivo para QR de monto abierto. | C3 | **Unit/componente:** el botón "Confirmar" está deshabilitado con importe vacío, 0 o negativo en monto abierto, y habilitado con importe > 0. **E2E:** no se emite `POST /payments` antes de confirmar. Comercio e importe son visibles antes de ese paso. |
| CA-3 | Crear pagos mediante W2 `POST /payments`, preservando `qrId` e idempotencia. | C4 | **Unit:** el cuerpo incluye el `qrId` recibido de W3. Un reintento reutiliza la misma clave y un intento nuevo genera otra. **E2E:** doble clic en "Confirmar" produce una sola creación efectiva o dos peticiones con la misma clave. |
| CA-4 | Consultar estado y recibos desde W2; los eventos del mock se entregan manualmente y no representan webhooks automáticos. | C4, C5 | **E2E:** tras crear un pago, "Actualizar estado" consulta W2 y refleja el estado. Sin acción manual el estado no cambia solo. **Revisión:** la UI no usa lenguaje de "notificación automática". |
| CA-5 | Mostrar y filtrar el historial localmente solo para pagos iniciados por este flujo, con fecha local registrada correctamente etiquetada. | C5 | **Unit:** solo se guardan pagos creados por C4. Los filtros operan sin llamadas de red. La etiqueta dice "fecha local registrada". **E2E:** con dos pestañas no hay duplicados. Una entrada corrupta en el almacenamiento no rompe la vista. |
| CA-6 | Guiar la recuperación ante QR inválido, desconocido, expirado o con conflicto de comercio/importe. | C6 (con C2/C4) | **Unit:** cada `code` de la sección 3 produce el mensaje y la acción esperados. **E2E:** con el mock configurado para cada escenario, la UI muestra la guía correspondiente y no deja un pago creado a medias. |
| CA-7 | Compilación, verificación del repositorio y E2E con el mock configurado; registrar resultados reales y limitaciones. | C7 | Ejecutar los comandos de build, verificación y E2E definidos por el repositorio (P-2). Adjuntar salidas reales (éxito y fallos) y una lista de limitaciones. No se aceptan resultados simulados. |

**Brecha de pruebas existentes:** el contexto no incluye las pruebas actuales. No sé qué pruebas cubren hoy un `POST` con cuerpo válido hacia W2 o W3. Declaro esto como brecha para que una persona la acepte o indique la cobertura existente. Si no hay cobertura, las pruebas de CA-1 y CA-3 son nuevas.

**Pruebas del API:** como la capa FastAPI no cambia (S-1), no se añaden pruebas en `api/tests/` para H03. Si P-1 revela que algún comportamiento debe vivir en FastAPI, se replantea el alcance antes de implementar.

---

## 5. Supuestos y preguntas pendientes

### 5.1 Supuestos adoptados (decisiones conservadoras)
- **S-1.** No hay cambios en `api/app/` (ver 1.4).
- **S-2.** No hay actualización de dependencias. Si se añade una librería QR, requiere versión exacta fijada, y si afecta al API se consulta PyPI/OSV con fecha y fuente.
- **S-4.** Formato de error unificado `{"code","message"}` y códigos HTTP de las secciones 3.2 y 3.3. Si el mock devuelve otros, la UI los traduce a estos códigos internos.
- **S-5.** Nombres de campos de las secciones 3.2 y 3.3 (`payload`, `qrId`, `amount`, `currency`, `reference`, `status`). Se confirman contra el mock.
- **S-6.** No hay identidad ni hash SHA-256 en esta historia (ver 2.1).
- **S-7.** El historial usa almacenamiento del navegador con `schemaVersion: 1`.
- **S-8.** El estado se actualiza solo por acción manual del usuario.

### 5.2 Preguntas pendientes
- **P-1.** ¿Cuál es el contrato real de W3 `/qrs/resolve` y W2 `/payments`, de estado y de recibo? Esto incluye campos, rutas, cabecera de idempotencia, códigos HTTP y formato de errores. Las fuentes son `design.md` y `spec.md` o el mock.
- **P-2.** ¿Cuál es la estructura de carpetas del frontend y qué comandos oficiales de build, verificación y E2E usa el repositorio?
- **P-3.** ¿Existe ya una librería de decodificación QR aprobada en el proyecto? Si no, ¿cuál se autoriza?
- **P-4.** ¿Cuál es la moneda y la unidad del importe (enteros en centavos o decimales)? ¿Hay límites máximos?
- **P-5.** ¿Existe ya alguna clave de almacenamiento local para historial que haya que respetar o migrar?
- **P-6.** ¿Hay un límite de tamaño del payload? Si existe, ¿cuál?
- **P-7.** El objetivo habla de que "el comercio" consulte referencia, estado y recibo, pero el historial es local a quien paga. ¿La vista es para la persona que pagó o existe un rol de comercio dentro de la aplicación?
- **P-8.** ¿El mock requiere credenciales (caso 401)?
- **P-9.** ¿Qué pruebas existentes cubren `POST` con cuerpo válido hacia W2/W3? Si ninguna, ¿se acepta la brecha?