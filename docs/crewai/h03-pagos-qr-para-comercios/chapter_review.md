# chapter_review.md

**H03 · Pagos QR para comercios — Revisión transversal del Issue**
Fecha: 2026-11-06 · Rol: Chapter (revisor transversal)

> **Alcance de este informe.** Es una auditoría documental de los entregables de Arquitectura, Backend, Frontend, Pruebas y Seguridad. No ejecuté ni afirmo haber ejecutado ningún comando, prueba, compilación ni consulta a PyPI/OSV. Todo resultado de ejecución es **NO EJECUTADO**. Este informe **no sustituye** ninguna aprobación humana.

---

## 1. Material revisado y limitaciones

| Elemento | Estado |
|---|---|
| `user_story.md` (Arquitecto) | Recibido, completo. |
| `backend_spec.md` y código `api/` | Recibido, completo. |
| `frontend_spec.md` y código Angular | Recibido, completo. |
| `testing_report.md` y pruebas pytest/Jasmine | Recibido, completo. |
| `security_report.md` | Recibido, completo. |
| OpenSpec (`proposal.md`, `design.md`, `spec.md`, `tasks.md`) | **No se incluyó su contenido** en el contexto. El contrato W2/W3 (P-1) es un supuesto común a todos los entregables y no puedo contrastarlo con la fuente. |
| Mock W2/W3, árbol real del repositorio, lockfile del frontend | No disponibles. |

No vi truncamiento del material entregado. La ausencia del OpenSpec y del mock se trata como limitación y condición previa al merge, no como motivo de rechazo.

### 1.1 Supuesto confirmado de stack

El stack decidido por el equipo es Python/FastAPI en `api/`. Las equivalencias legadas del Issue quedan así:

| Referencia legada | Traducción explícita en los entregables | Valoración |
|---|---|---|
| `PreparedStatement` | No hay SQL ni base de datos (Backend §7). La persistencia es `localStorage` en el navegador. | N/A, coherente. |
| `mvn test` | `python tools/lab.py test api` (Backend y Pruebas). | Traducido y coherente. |
| `auth/src/main/java` | `api/app/` (Arquitecto S-1/C8, Backend §2). | Traducido y coherente. |

Backend afirma que no usa Java, Quarkus ni Maven, y ningún entregable mezcla stacks. El frontend es Angular, que es el cliente de navegador que exige el Issue, no otro stack del API. **No hay motivo de rechazo por stack.** Se registra como supuesto confirmado.

---

## 2. Cobertura por criterio de aceptación

Leyenda: ● diseño y prueba asociados · ◐ parcial · ○ sin cobertura. Todas las pruebas están **NO EJECUTADAS**.

| CA | Arquitectura | Persistencia | Implementación | Pruebas | Seguridad | Valoración |
|---|---|---|---|---|---|---|
| **CA-1** Decodificar en navegador y enviar solo el payload a W3 | ● C1/C2, `payload` | N/A | ● `QrDecoderService` (motor `BarcodeDetector`, token `QR_IMAGE_ENGINE`), `QrApiService.resolve` | ● `FE-DEC-01…06`, `FE-SVC-01`, `FE-PAGO-01`, `MOCK-01/02/07`, `E2E-01/09` | ◐ H-10 (sin límite de tamaño de archivo ni de payload, P-6) | Diseño cubierto. Limitación: `BarcodeDetector` no existe en todos los navegadores y P-3 está abierto. |
| **CA-2** Mostrar comercio e importe antes de confirmar; importe positivo en monto abierto | ● C3 | N/A | ● fase `review`, `positiveAmount`, `canConfirm` | ● `FE-PAGO-02…06`, `E2E-02/03` | ◐ H-02 (el cliente decide importe y moneda; el servidor debe forzarlos) | Cubierto. |
| **CA-3** Crear pagos con W2 `POST /payments`, preservando `qrId` e idempotencia | ● C4, `Idempotency-Key` supuesta | N/A | ● `confirm()` síncrono, clave por intento enlazada a `qrId+importe+moneda` | ● `FE-SVC-06/07`, `FE-PAGO-07…10`, `MOCK-08…11/14`, `E2E-04` | ◐ H-03 (la clave solo vive en memoria), H-02 | Cubierto para el reintento dentro del mismo intento. Ver O-03. |
| **CA-4** Estado y recibos desde W2; eventos manuales, sin webhooks | ● C4, regla S-8 | N/A | ● «Actualizar estado» y «Ver recibo» manuales, sin polling | ● `FE-SVC-08/09`, `FE-PAGO-11/12/19`, `FE-HIST-07…09`, `MOCK-12/13/15`, `E2E-05` | ◐ H-01 (autorización sin demostrar), H-04 (recibo sin lista de campos) | Cubierto. Rutas de estado y recibo supuestas (P-1). |
| **CA-5** Historial local, filtrable, solo de este flujo, con fecha local etiquetada | ● C5, `schemaVersion: 1` | ● clave `merchantQrPayments.history`, deduplicación, datos corruptos, esquema ajeno sin sobrescribir | ● `PaymentHistoryService`, columna «Fecha local registrada» | ● `FE-STO-01…09`, `FE-HIST-01…06`, `FE-PAGO-11/17`, `E2E-06/07` | ◐ H-05 (claro, sin borrado ni CSP), H-06 (`paymentId` sin validar) | Cubierto. |
| **CA-6** Recuperación ante QR inválido, desconocido, expirado o conflicto | ● C6, tabla §3.2/§3.3 | N/A | ● `error-messages.ts`, descarte de la revisión en `QR_EXPIRED`/`QR_CONFLICT`, «Volver a validar el QR» | ● `FE-ERR-01…09`, `FE-PAGO-13…16/18`, `MOCK-03…06/14`, `E2E-08` | ● el mensaje del servicio se muestra como texto plano | Cubierto. |
| **CA-7** Compilación, verificación del repo y E2E con el mock; resultados reales y limitaciones | ● C7 | N/A | ◐ comandos de frontend supuestos (P-2); solo `python tools/lab.py test api` está confirmado | ◐ plan completo y registro §9, pero **sin salidas reales** | ◐ H-07 (OSV/`pip-audit`/`npm audit` sin ejecutar) | **Pendiente de ejecución humana.** E2E headless en Linux/Windows limitado por P-3 (L-1). |

**Criterios sin diseño ni prueba asociada: ninguno.** Los siete criterios tienen diseño y prueba definidos. La evidencia de CA-7 no puede existir hasta que una persona ejecute.

---

## 3. Consistencia de contratos y supuestos entre entregables

| Contrato / supuesto | Arquitecto | Backend | Frontend | Pruebas | Seguridad | Resultado |
|---|---|---|---|---|---|---|
| W3 `POST /qrs/resolve` con `{payload}` | §3.2 | no implementa (externo) | `QrApiService.resolve` | `FE-SVC-01`, `MOCK-01…07` | H-01/H-02 parten del mismo supuesto | Consistente (supuesto P-1). |
| W2 `POST /payments` con `{qrId, amount, currency}` y `Idempotency-Key` | §3.3 | no implementa | `createPayment` | `FE-SVC-06`, `MOCK-08…11` | H-02/H-03 | Consistente (supuesto P-1). |
| Rutas de estado y recibo (`GET /payments/{id}` y `/receipt`) | no determinables | no implementa | supuestas | T-2 las repite | H-01/H-06 | Consistente. Requiere validación contra el mock. |
| Códigos de negocio (`QR_*`, `AMOUNT_INVALID`, `IDEMPOTENCY_CONFLICT`) | S-4 | los traduce el frontend; usa códigos genéricos (`CONFLICT`, etc.) | `error-messages.ts` | `FE-ERR-*`, `MOCK-*` | — | Consistente. Los códigos genéricos del backend no se mezclan con los de negocio. |
| Persistencia local `schemaVersion: 1` | §2.1, S-7 | delega al frontend | `PaymentHistoryService` | `FE-STO-*` | H-05 | Consistente. |
| **La capa FastAPI no cambia en H03 (S-1, C8: no se añaden `main.py`, `routers/`, `services.py`, `schemas.py` ni `config.py`)** | **Declarado** | **Entrega justamente esos archivos, más `errors.py` y `requirements.txt`** | "no hay cambios en `api/app/`" | Pruebas `API-*`, `ERR-*`, `PER-*`, `DEP-*` sobre ese andamiaje | H-07/H-08/H-09 revisan ese código | **CONTRADICCIÓN. Ver B-1.** |

---

## 4. Bloqueantes de diseño (motivo de RECHAZADO)

### B-1 · El Backend entrega código fuera del alcance del Issue y contradice el plan aprobado de Arquitectura

**Evidencia**
- `user_story.md` §1.4 S-1, §2 C8 y §4: la capa FastAPI **no cambia**, y "no se añaden `main.py`, `routers/`, `services.py`, `schemas.py` ni `config.py` nuevos para H03". También S-2: no se actualizan dependencias ni hay pins que definir.
- El Issue no pide endpoints nuevos ni persistencia en servidor, y el mock es de solo lectura.
- `backend_spec.md` §1 y §2 lo reconoce ("no implemento ningún endpoint de negocio") y aun así entrega `api/requirements.txt` con pines **no verificados** (`fastapi==0.115.6`, `starlette==0.41.3`, `pydantic==2.10.3`, `uvicorn==0.32.1`), `config.py`, `schemas.py`, `services.py`, `errors.py`, `main.py`, `routers/health.py` y un endpoint `GET /health` que el propio Backend califica de "fuera del contrato de H03". Lo justifica como "base mínima" para tener "un caso válido comprobable".
- Pruebas (`testing_report.md` §12) construye cuatro archivos sobre ese andamiaje: `test_h03_health_contract.py`, `test_h03_error_format.py`, `test_h03_no_server_persistence.py` y `test_h03_dependency_pins.py`. Ninguno prueba un criterio de aceptación de H03.
- Seguridad dedica H-07, H-08 y H-09 a ese código añadido.
- Desconocemos si `api/app/` y `api/requirements.txt` ya existen. Backend pide "no sobrescribir" y Pruebas lo trata como T-3. El riesgo de pisar archivos existentes o fijar dependencias propias queda abierto.

**Por qué es bloqueante.** Es un cambio fuera del alcance del Issue y un supuesto que se contradice entre entregables (Arquitectura frente a Backend). Además introduce un cambio de dependencias que el Issue no pide.

**Responsable:** Backend (retirada o justificación) y Arquitecto (decisión de alcance). La aprobación final es de una persona.

**Cambio requerido (una de las dos vías):**
1. **Recomendada.** Retirar de la entrega de H03 `api/app/*` (todos los archivos nuevos), `api/requirements.txt` y las cuatro pruebas `API/ERR/PER/DEP`. El Backend declara "sin cambios en `api/`" y Pruebas conserva solo lo que verifica criterios (`MOCK-*`, `FE-*`, `E2E-*`). Con ello H-07, H-08 y H-09 dejan de aplicar a este Issue y pasan a un issue propio.
2. Si la persona responsable decide conservar el andamiaje, **actualizar `user_story.md`** (S-1, C8, §4) para reflejar el cambio de alcance. Además, aprobar explícitamente `/health` y los pines de `requirements.txt`, con consulta OSV/PyPI y fecha, y vincular el cambio al Issue.

**Cómo verificarlo**
```bash
# NO EJECUTADO — vía 1: no debe haber cambios en api/ ni en requirements
git diff --stat <base>..HEAD -- api/app api/requirements.txt api/tests/test_h03_health_contract.py \
  api/tests/test_h03_error_format.py api/tests/test_h03_no_server_persistence.py api/tests/test_h03_dependency_pins.py
# esperado: sin salida
```
Para la vía 2, `user_story.md` debe mostrar un S-1/C8 coherente con los archivos entregados y una aprobación humana registrada del cambio de alcance.

---

## 5. Observaciones (no bloqueantes de diseño por sí solas)

| ID | Observación | Responsable | Cambio requerido | Cómo verificarlo (NO EJECUTADO) |
|---|---|---|---|---|
| **O-01** (H-01, Alta condicional) | Estado y recibo se consultan sin identidad demostrada y el rol de comercio no existe (P-7, P-8). Ninguna prueba cubre acceso con otra identidad. | Arquitecto (decisión P-7/P-8), equipo de W2/mock (control de pertenencia), Pruebas (`MOCK-16/17`) | Decidir si la vista es del pagador o hay rol de comercio. Si el mock no tiene identidades, registrarlo como **limitación abierta**, no como aprobado. No declarar cumplida la mitad "comercio" de la historia sin esa decisión. | `curl` con dos identidades propuesto en `security_report.md` H-01. Esperado: B no recibe datos de A. |
| **O-02** (H-02, Alta condicional) | El importe y la moneda los decide el cliente, también en QR fijo. `MOCK-11` solo cubre importe ≤ 0. | Pruebas (nueva prueba), equipo de W2/mock (servidor fuerza importe), Frontend (tope y precisión tras P-4) | Añadir `MOCK-16b` (importe o moneda distintos al QR fijo). Definir unidad y límites (P-4). | `python -m pytest api/tests/test_h03_mock_contract.py -k mock_16b`. Esperado: 409/422. Un 200/201 confirma el hallazgo. |
| **O-03** (H-03, Media) | La clave de idempotencia se pierde al recargar, o al volver a elegir el mismo QR tras un resultado ambiguo (red caída o 5xx), con riesgo de cobro duplicado. `FE-PAGO-09` solo cubre la misma instancia. | Frontend | Persistir el intento pendiente en `sessionStorage` con huella `qrId\|importe\|moneda`. Mostrar un aviso tras resultado ambiguo. Controlar la ausencia de `crypto`. | Spec nueva `FE-PAGO-20`: la misma clave tras recrear el componente. E2E con mock apagado y recarga. |
| **O-04** (H-04, Media) | El recibo muestra todos los campos recibidos, sin lista permitida. | Frontend y Arquitecto (campos públicos en `design.md`) | Lista de campos permitidos con etiquetas fijas. Sustituir `FE-HIST-08`. | `FE-HIST-10`: los campos no listados no se renderizan. |
| **O-05** (H-05/H-06/H-10, Media-Baja) | Historial en claro sin opción de borrado ni CSP. `paymentId` sin validar de formato. Sin límite de archivo ni de payload (P-6). | Frontend (borrado, `SAFE_ID`, límites), responsable del despliegue (CSP) | `clearAll()` y botón de borrado. Validación de `paymentId`. Límite de tamaño y de payload. Actualizar `FE-SVC-08`. | `FE-STO-10`, specs de `SAFE_ID`, `FE-DEC-07`, `FE-PAGO-21`. `curl -sI <app>` para CSP. |
| **O-06** (H-11, Informativa) | Orígenes W2/W3 configurables, sin definición de CORS, CSP ni credenciales. | Arquitecto y responsable del despliegue | Definir las bases solo en la configuración de compilación. Si hay CORS, lista explícita de orígenes. | Revisión de configuración; `OPTIONS` con `Origin` ajeno. |
| **O-07** | Las pruebas `MOCK-*` están en `api/tests/` y **fallan** (no se omiten) si faltan las variables `H03_*`. Si `python tools/lab.py test api` las incluye, la suite oficial queda en rojo para quien no tenga el mock configurado. | Pruebas | Ubicarlas o marcarlas de modo que se ejecuten solo con el mock configurado, sin romper la suite estándar. Documentar el criterio de skips. | `python tools/lab.py test api` sin variables: debe comportarse según lo decidido. Registrar la salida. |
| **O-08** (P-3, limitación de CA-1/CA-7) | Sin librería QR aprobada, solo funciona `BarcodeDetector`. Los E2E no pueden correr en navegadores sin esa API, ni en Chromium headless sobre Linux. | Arquitecto (decisión P-3), Frontend | Aprobar una librería con versión exacta en el lockfile y proveerla vía `QR_IMAGE_ENGINE`, o aceptar y registrar por escrito la limitación. | E2E-01…08 en un navegador compatible, con capturas de red. |
| **O-09** | El Frontend entrega `app.component.ts` y `app.routes.ts` completos y el Arquitecto no conoce la estructura (P-2). Podrían sobrescribir los existentes. | Frontend | Integrar las rutas y la navegación sobre los archivos reales, sin reemplazarlos. | `git diff -- src/app/app.component.ts src/app/app.routes.ts` solo debe mostrar las adiciones de H03. |
| **O-10** (P-1) | El contrato W2/W3 completo es supuesto y no se contrastó con `design.md`, `spec.md` ni con el mock. | Arquitecto y Pruebas | Contrastar los campos, rutas, cabecera de idempotencia y códigos con las fuentes y ajustar `qr-pagos.config.ts` y `qr-api.service.ts`. | `MOCK-01…15` con el mock configurado. Un fallo por contrato distinto es hallazgo de P-1. |
| **O-11** (H-07) | Los pines del API no están verificados contra OSV/PyPI. `pytest` y `httpx` no están fijados. Si B-1 se resuelve por la vía 1, esto sale del alcance de H03. | Seguridad / Arquitecto | Si se mantiene el andamiaje: consultar OSV/PyPI y registrar fecha y fuente. Si no, trasladarlo al issue propio. | `pip install -r requirements.txt && pip check && pip-audit -r requirements.txt`; `npm audit --omit=dev` para el frontend. |

Pendientes abiertos de Arquitectura que condicionan lo anterior: P-2, P-4, P-5, P-6, P-7, P-8 y P-9 siguen **sin respuesta humana**.

---

## 6. Pruebas pendientes y condiciones previas al merge

Estas condiciones **no son motivo de rechazo por sí solas**. Sin ellas la aprobación final no puede darse. Todos los comandos están **NO EJECUTADOS**; la persona responsable adjunta la salida literal en `evidencia/` con fecha y hash del commit.

| # | Condición | Responsable | Comando exacto | Esperado |
|---|---|---|---|---|
| C-1 | Suite oficial del repositorio | Persona de Pruebas | `python tools/lab.py test api` | Verde, 0 skips |
| C-2 | Specs Angular H03 (comando supuesto, P-2) | Persona de Pruebas | `npx ng test --watch=false --browsers=ChromeHeadless` | `FE-DEC/SVC/ERR/STO/PAGO/HIST` verdes, 0 skips |
| C-3 | Instalación y compilación del frontend (supuesto, P-2) | Persona de Pruebas | `npm ci` y `npm run build` | Sin errores |
| C-4 | Verificación del repositorio (nombre del script según P-2) | Persona de Pruebas | `npm run <script-de-verificacion>` | Verde |
| C-5 | Contrato contra el mock configurado, con variables `H03_*` rellenas | Persona de Pruebas | `cd api && python -m pytest tests/test_h03_mock_contract.py -v -rs` | `MOCK-01…15` verdes; un fallo por contrato se registra contra P-1 |
| C-6 | E2E manuales con el mock | Persona de Pruebas | `E2E-01…09` de `testing_report.md` §8.6, con capturas del panel de red | Resultados conforme al informe; limitaciones registradas (L-1) |
| C-7 | Consulta de vulnerabilidades (según B-1) | Seguridad | `pip-audit -r api/requirements.txt` (solo si se mantiene `requirements.txt`) y `npm audit --omit=dev` | Sin avisos aplicables o decisión registrada |
| C-8 | Aprobaciones humanas | Responsables del equipo | n/a | Ver §8 |

Orden obligatorio: línea base primero, cambio después. Un `skip` cuenta como no cumplido.

---

## 7. Evidencia y registro

| Verificación | Realizada | Evidencia |
|---|---|---|
| Lectura cruzada de los cinco entregables contra los siete criterios | Sí (documental) | Este informe, §2 y §3 |
| Comparación del plan del Arquitecto con los archivos del Backend | Sí (documental) | `user_story.md` S-1/C8/§4 frente a `backend_spec.md` §2 y §12 de `testing_report.md` |
| Cualquier comando, prueba, compilación o consulta OSV/PyPI | **No** | **NO EJECUTADO**; sin salida real en este flujo |

No afirmo que el código funcione ni que haya cobertura. CA-1…CA-7 permanecen **NO EJECUTADOS**.

---

## 8. Aprobaciones humanas

Este informe no aprueba ni sustituye aprobaciones. Quedan pendientes y a cargo de personas:
- Decisión de alcance sobre `api/` (B-1).
- Respuestas a P-1 a P-9, en especial P-3, P-7 y P-8.
- Aprobación de cualquier librería QR con versión exacta.
- Revisión y aceptación de las salidas reales de las pruebas y de las limitaciones registradas.
- Aprobación final del merge.

---

## 9. Veredicto

**Resumen.** Los siete criterios de aceptación tienen diseño en Arquitectura, implementación en el frontend y pruebas asociadas. No hay marcadores sin resolver (`<VERSIÓN_...>`, `[Pendiente]` en una decisión necesaria). El supuesto de stack Python/FastAPI está traducido de forma coherente. No hay mezcla de stacks.

**Bloqueante de diseño**
- **B-1:** el Backend entrega y las Pruebas y Seguridad auditan un andamiaje en `api/` (`main.py`, `config.py`, `schemas.py`, `services.py`, `errors.py`, `routers/health.py`, `requirements.txt` con pines sin verificar y `GET /health`) que el Arquitecto excluyó expresamente (S-1, C8, S-2) y que el Issue no pide. Es un cambio fuera de alcance y una contradicción entre entregables.

**Condiciones previas al merge (no bloquean el diseño):** C-1 a C-8 de la sección 6, con la evidencia ejecutada por una persona.

**Correcciones requeridas para levantar el rechazo:**
1. Resolver B-1 por la vía 1 (retirar el andamiaje y sus pruebas) o por la vía 2 (actualizar el plan, aprobar `/health` y los pines con consulta OSV/PyPI).
2. Tras ello, tratar O-01 a O-11, con prioridad para O-03 (idempotencia tras recarga), O-01/O-02 (autorización e importe en servidor), O-04 (recibo) y O-07 (suite oficial en rojo sin mock).

Una vez resuelto B-1 y sin otros bloqueantes de diseño, este revisor recomienda volver a emitir un veredicto **APROBADO** que dependa de la evidencia ejecutada.

VEREDICTO: RECHAZADO — bloqueante de diseño B-1: el Backend añade código y dependencias en `api/` (andamiaje FastAPI, `/health`, `requirements.txt` con pines no verificados) y se prueba con cuatro archivos `API/ERR/PER/DEP`, lo cual contradice el plan del Arquitecto (S-1, C8, S-2) y queda fuera del alcance del Issue. Los siete criterios de aceptación sí tienen diseño y prueba asociados; ninguna prueba se ejecutó (NO EJECUTADO). La aprobación final depende de resolver B-1, de la evidencia ejecutada por una persona (C-1 a C-7) y de las aprobaciones humanas pendientes.