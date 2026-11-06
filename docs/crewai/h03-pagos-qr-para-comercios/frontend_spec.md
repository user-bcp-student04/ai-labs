# frontend_spec.md

## 1. Alcance

**El frontend sí cambia.** El Issue H03 pide un recorrido de usuario en el navegador: decodificar la imagen QR, validar comercio e importe, confirmar el pago, consultar estado y recibo, y mostrar un historial local. Por eso se entregan componentes, servicios y rutas Angular 17 standalone.

Fuera de alcance (según el Issue):
- No se modifica el mock, que es de solo lectura.
- No se genera QR ni se escanea con cámara.
- No se tratan los eventos del mock como webhooks automáticos.
- No hay cambios en `api/app/`, según el plan del Arquitecto (S-1) y la nota del Backend.
- No se regeneran `main.ts`, `index.html`, `package.json` ni `angular.json`.

Nada de lo descrito aquí se ha ejecutado. Los resultados de la sección 11 son **NO EJECUTADO**.

## 2. Contrato consumido

Ni el Arquitecto ni el Backend recibieron los esquemas reales de W2 y W3 (pendiente P-1). El frontend usa el **contrato de trabajo supuesto** del Arquitecto y lo concentra en dos archivos para poder ajustarlo sin tocar los componentes: `qr-pagos.config.ts` (rutas y URLs base) y `qr-api.service.ts` (cabecera y validación de respuestas).

| Operación | Método y ruta | Cuerpo / cabeceras | Respuesta esperada | Origen |
|---|---|---|---|---|
| Resolver QR (W3) | `POST /qrs/resolve` | `{ "payload": "<texto>" }`, sin imagen | `{ qrId, merchant:{name}, amountType:'fixed'\|'open', amount?, currency }` | Ruta explícita en el Issue; campos supuestos |
| Crear pago (W2) | `POST /payments` | `{ qrId, amount, currency }` más cabecera `Idempotency-Key` | `{ paymentId, reference, status, qrId }` | Ruta explícita; campos y cabecera supuestos |
| Consultar estado (W2) | `GET /payments/{paymentId}` | ninguno | objeto con `status` (texto) | **Ruta supuesta** (P-1) |
| Consultar recibo (W2) | `GET /payments/{paymentId}/receipt` | ninguno | objeto; se muestra tal cual, campo a campo | **Ruta supuesta** (P-1) |
| Errores | cualquiera | cuerpo `{ "code", "message" }` | ver sección 6 | Supuesto S-4 |

- **URLs base:** los tokens `W3_BASE_URL` y `W2_BASE_URL` tienen valor por defecto `''` (mismo origen, por ejemplo vía proxy de desarrollo). Se pueden sobrescribir con `providers`.
- **Importe:** moneda y unidad no están definidas (P-4). La UI muestra el importe y la moneda tal como llegan, sin formatear ni convertir.
- **Recibo:** como su esquema es desconocido, se lista cada campo recibido (nombre del campo y valor) sin interpretarlo.

## 3. Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `src/app/app.component.ts` | Cabecera con navegación y `<router-outlet>` |
| `src/app/app.routes.ts` | Rutas `/pagar-qr` y `/historial`. Provee `HttpClient` y los servicios a nivel de ruta |
| `src/app/qr-pagos/qr-pagos.models.ts` | Tipos y clase `ApiError` |
| `src/app/qr-pagos/qr-pagos.config.ts` | URLs base y rutas de estado y recibo (supuestas) |
| `src/app/qr-pagos/qr-pagos.styles.ts` | Estilos compartidos: foco visible, alertas, `.sr-only` |
| `src/app/qr-pagos/qr-decoder.service.ts` | Decodificación del QR en el navegador |
| `src/app/qr-pagos/qr-api.service.ts` | Clientes W3 y W2, validación de respuestas, normalización de errores |
| `src/app/qr-pagos/error-messages.ts` | Mapa de errores a mensajes y acciones de recuperación |
| `src/app/qr-pagos/payment-history.service.ts` | Historial local con `schemaVersion: 1` |
| `src/app/qr-pagos/qr-pago.component.ts` y `.html` | Recorrido: cargar, revisar, confirmar, resultado |
| `src/app/qr-pagos/historial.component.ts` y `.html` | Historial local, filtros, actualizar estado, ver recibo |

**Inyección de dependencias:** los servicios no usan `providedIn: 'root'`. Se declaran en `providers` de la ruta padre en `app.routes.ts`, junto con `provideHttpClient()`. Así el recorrido no depende de que `main.ts` ya provea `HttpClient`. Si `main.ts` ya lo provee, la duplicación es inocua.

## 4. Recorrido de usuario

**Pantalla `/pagar-qr`:**
1. **Cargar imagen.** La persona elige un archivo de imagen. El navegador lo decodifica y solo el texto del QR viaja a W3. La imagen nunca se envía.
2. **Validar.** `POST /qrs/resolve`. Mientras tanto se muestra «Validando el QR…».
3. **Revisar.** Se muestran comercio, tipo de importe e importe **antes** de cualquier cobro.
   - QR de importe fijo: se muestra el importe del QR, que no se edita.
   - QR de monto abierto: aparece el campo «Importe a pagar» y el botón queda deshabilitado hasta que el importe sea mayor que 0.
4. **Confirmar.** Es una acción explícita. Hace `POST /payments` con `qrId`, importe, moneda y `Idempotency-Key`.
5. **Resultado.** Se muestran referencia, ID de pago y estado. El estado solo cambia con «Actualizar estado», que consulta W2 de forma manual.
6. **Historial** (`/historial`). Lista los pagos iniciados por este flujo, con filtros locales, «Actualizar estado» y «Ver recibo».

El recorrido tiene seis fases internas: `idle`, `decoding`, `resolving`, `review`, `submitting` y `success`.

## 5. Campos y validaciones

| Campo | Tipo | Validación | Mensaje |
|---|---|---|---|
| Imagen del código QR | `input type=file`, `accept="image/*"` | Debe ser imagen y contener un QR legible | Ver sección 6, errores de lectura |
| Importe a pagar (solo monto abierto) | `input type=number` | Obligatorio y número finito mayor que 0 | Vacío: «Ingresa el importe a pagar.» Cero, negativo o inválido: «El importe debe ser un número mayor que 0.» |
| Importe de QR fijo | solo lectura | Debe ser > 0 | «El QR trae un importe no válido; no se puede confirmar.» |
| Filtro de texto (historial) | texto | Ninguna. Busca en referencia, comercio e ID de pago | n/d |
| Filtro de estado (historial) | select | Valores presentes en el historial | n/d |

- Como no hay límite de tamaño de payload definido (P-6), el frontend no impone uno. Solo gestiona la respuesta 413 del servicio.
- La validación del cliente no sustituye la del servidor (W2/W3).

## 6. Mensajes y recuperación

Cada error se muestra en un bloque `role="alert"` con título, explicación, acción sugerida y, si existe, el «Detalle del servicio» (`message` de la API, como texto plano).

| Origen | Situación | Título | Acción |
|---|---|---|---|
| Lectura local | Navegador sin `BarcodeDetector` | «Tu navegador no puede leer QR desde imágenes» | Usar un navegador compatible o aprobar una librería (P-3) |
| Lectura local | Archivo no es imagen | «El archivo no es una imagen» | Elegir otra imagen |
| Lectura local | Sin QR en la imagen | «No se encontró un QR en la imagen» | Elegir otra imagen |
| Lectura local | Imagen ilegible | «No se pudo leer la imagen» | Elegir otra imagen |
| `QR_INVALID` (400) | QR inválido | «El código QR no es válido» | Elegir otra imagen |
| `QR_UNKNOWN` (404) | QR desconocido | «QR no reconocido» | Elegir otra imagen |
| `QR_EXPIRED` (410) | QR expirado | «El QR expiró» | Pedir un QR vigente y cargarlo. Se descarta la revisión actual |
| `QR_CONFLICT` (409) | Conflicto de comercio o importe | «Los datos del comercio o del importe cambiaron» | Botón «Volver a validar el QR». No se confirma con datos previos |
| `AMOUNT_INVALID` (422) | Importe no válido | «Importe no válido» | Corregir el importe |
| `IDEMPOTENCY_CONFLICT` (409) | Clave reutilizada con otro cuerpo | «Solicitud repetida con datos distintos» | Se descarta la clave. La próxima confirmación genera una nueva |
| `PAYLOAD_TOO_LARGE` (413) | Payload demasiado grande | «El contenido del QR es demasiado grande» | Elegir otro QR |
| 401 / 403 | Sin autorización | «No tienes autorización» | Mensaje genérico |
| 404 en estado o recibo | Pago o recibo no encontrado | «No se encontró el pago o el recibo» | Reintentar más tarde |
| Sin conexión (status 0) | Red caída o mock apagado | «Sin conexión con el servicio» | Reintentar. Si era un pago, se reutiliza la misma clave de idempotencia |
| 5xx | Fallo del servicio | «El servicio no pudo procesar la solicitud» | Reintentar |
| Respuesta fuera de contrato | Campos ausentes | «Respuesta inesperada del servicio» | No se muestra ningún pago como creado |
| Otro código | Cualquier otro | «No se pudo completar la operación» | Se muestra el `message` de la API o el código |

## 7. Estados por pantalla

**`/pagar-qr`**
- **Carga:** «Leyendo la imagen…», «Validando el QR…» y «Confirmando pago…». Usan `role="status"` y `aria-live="polite"`. Se deshabilitan el selector de archivo y el botón de confirmar.
- **Vacío / inicial:** solo el paso 1 con su ayuda. No hay revisión ni botón de pago.
- **Éxito:** «Pago creado» con referencia, ID, estado y comercio. Muestra el aviso «El estado no cambia solo…» y los botones «Actualizar estado», «Ver historial» y «Pagar otro QR».
- **Error:** bloque `role="alert"` según la sección 6. Si no se pudo guardar en el historial local, se muestra un aviso aparte sin ocultar el éxito del pago.

**`/historial`**
- **Carga:** «Consultando estado…» y «Consultando recibo…» durante las consultas manuales. Todos los botones de acción se deshabilitan mientras tanto.
- **Vacío:** «Aún no hay pagos QR iniciados desde esta aplicación», con enlace a pagar. Si hay datos pero el filtro no coincide: «Ningún pago coincide con el filtro» y botón «Limpiar filtros».
- **Éxito:** tabla con comercio, referencia, importe, estado, **«Fecha local registrada»** y acciones. El recibo se muestra en un panel con botón «Cerrar recibo».
- **Error:** bloque `role="alert"` con las guías de estado y recibo.

## 8. Prevención de envíos duplicados e idempotencia

- `confirm()` cambia a la fase `submitting` de forma **síncrona**, antes de la petición. Un segundo clic o Enter se descarta porque la fase ya no es `review`. El botón además queda deshabilitado.
- Cada intento de confirmación tiene una `Idempotency-Key` (UUID) enlazada a `qrId + importe + moneda`.
  - Si un intento falla por red o por 5xx, el reintento con los mismos datos **reutiliza la clave**.
  - Si cambia el importe o el QR, o el servidor responde `IDEMPOTENCY_CONFLICT`, `QR_EXPIRED` o `QR_CONFLICT`, se genera una clave nueva en el siguiente intento.
- El `qrId` enviado es exactamente el recibido de W3.
- No hay reintentos automáticos de `POST /payments` ni polling. «Actualizar estado» tampoco se repite solo.
- La selección de archivo se ignora mientras haya una operación en curso.

## 9. Historial local

- **Almacén:** `localStorage`, clave `merchantQrPayments.history`, formato `{ "schemaVersion": 1, "entries": [...] }`.
- **Solo pagos de este flujo:** únicamente se guardan pagos que `POST /payments` creó desde el componente de pago. No se consulta ningún listado remoto.
- **Campos por entrada:** `paymentId`, `reference`, `status`, `qrId`, `merchantName`, `amount`, `currency` y `registeredAtLocal`.
- **`registeredAtLocal`:** fecha ISO tomada del reloj del dispositivo al registrar el pago. Se etiqueta como **«Fecha local registrada»** y no es una fecha informada por W2.
- **Varias pestañas:** cada escritura lee, modifica y escribe, deduplicando por `paymentId`. El evento `storage` refresca la lista.
- **Datos corruptos:** las entradas con forma inválida se ignoran sin romper la pantalla.
- **Datos ajenos:** si la clave contiene un esquema distinto o JSON ilegible, no se sobrescribe. El pago sigue siendo válido y se avisa de que no se pudo guardar en el historial (P-5).
- **Filtros:** se calculan en memoria, sin llamadas de red.
- **Rol de comercio (P-7):** la vista es la de la aplicación que inició el pago. No se ha definido un rol de comercio separado.

## 10. Accesibilidad

- Todos los controles tienen `<label>` asociada. Los textos de ayuda y de error se enlazan con `aria-describedby`, y el campo de importe usa `aria-invalid`.
- Todo es operable con teclado: enlaces, botones, `select` y `input`. Los formularios se envían con Enter.
- El foco visible es un contorno de 3 px en `:focus-visible` para enlaces, botones, inputs y selects, definido en `QR_STYLES`.
- Gestión de foco: tras un error el foco va al bloque de alerta, y tras validar el QR va al encabezado de revisión. Tras confirmar el pago va al encabezado del resultado, y al abrir un recibo va a su panel.
- Los estados de carga y los resultados usan `role="status"`/`aria-live="polite"`. Los errores usan `role="alert"`.
- Los botones de las filas del historial incluyen la referencia en `aria-label`. La tabla tiene `<caption>` visible solo para lectores de pantalla.
- La navegación principal tiene `aria-label` y `aria-current="page"` en el enlace activo.
- El estado nunca se transmite solo por color.

## 11. Cómo comprobar el recorrido y sus errores

Todo **NO EJECUTADO**. Quien lo ejecute debe conservar las salidas reales.

**Preparación**
1. Instala y compila con los comandos oficiales del repositorio (P-2), por ejemplo `npm ci` y `npm run build`. Anota la salida real.
2. Configura el mock de W2/W3 (solo lectura) y haz que el origen de la app lo alcance con las rutas `/qrs/resolve` y `/payments`, por ejemplo mediante proxy.
3. Si el mock está en otro origen, sobrescribe `W3_BASE_URL` y `W2_BASE_URL`.
4. Usa un navegador con `BarcodeDetector` para QR (por ejemplo Chrome en macOS o Android).

**Caso válido, QR de importe fijo**
1. Abre `/pagar-qr` y carga una imagen QR válida.
2. En el panel de red, `POST /qrs/resolve` lleva solo `{"payload": "..."}` y no hay datos de imagen.
3. Comercio e importe aparecen antes de confirmar y no hay `POST /payments` todavía.
4. Pulsa «Confirmar pago» **dos veces rápido**. Debe salir un solo `POST /payments` con `qrId` y `Idempotency-Key`.
5. Se muestran referencia y estado. Sin acciones, el estado no cambia.
6. Pulsa «Actualizar estado» y comprueba que se hace `GET` a W2 y se refleja el estado.

**Caso válido, monto abierto**
1. Carga un QR de monto abierto. Aparece el campo de importe.
2. Con campo vacío, `0` o `-5`, el botón está deshabilitado y se muestra el mensaje.
3. Con `10`, se habilita. Confirma y comprueba que `amount` en el cuerpo coincide.

**Historial**
1. Abre `/historial` y verifica que aparece el pago con «Fecha local registrada».
2. Filtra por texto y por estado, y comprueba que no hay peticiones de red.
3. Pulsa «Ver recibo» y comprueba que se muestran los campos del recibo.
4. Abre `/historial` en dos pestañas, crea un pago en una y confirma que la otra se actualiza sin duplicados.
5. Escribe basura en la clave `merchantQrPayments.history` y recarga. La pantalla no debe romperse, y se mostrará el aviso al intentar guardar.

**Errores**

Configura el mock para cada escenario:

| Escenario | Resultado esperado |
|---|---|
| `QR_INVALID` | Mensaje de QR inválido y acción de elegir otra imagen |
| `QR_UNKNOWN` | QR no reconocido |
| `QR_EXPIRED` en resolve y en payments | «El QR expiró». Se descarta la revisión |
| `QR_CONFLICT` en resolve y en payments | Botón «Volver a validar el QR». No se confirma con datos previos |
| `AMOUNT_INVALID` | Mensaje de importe |
| `IDEMPOTENCY_CONFLICT` | Mensaje de solicitud repetida y clave nueva en el siguiente intento |
| 413 | Mensaje de payload demasiado grande |
| 401 | Mensaje de autorización |
| Mock apagado (status 0) | «Sin conexión». Al reintentar el pago se reutiliza la misma clave |
| 5xx | Mensaje del servicio |
| Imagen sin QR o archivo no imagen | Mensajes de lectura local |

**Pruebas automáticas:** no se incluyen en este entregable (corresponden al rol de Pruebas). La verificación del repositorio y los E2E con el mock (CA-7) deben ejecutarse y registrarse con su salida real.

## 12. Limitaciones y pendientes

- **Decodificación QR (P-3):** no se añade ninguna dependencia. El motor por defecto es la API nativa `BarcodeDetector`.
  - No está disponible en Firefox ni en Safari de escritorio, y tampoco en Chrome para Windows o Linux, entre otros. En esos casos la UI muestra el mensaje «Tu navegador no puede leer QR desde imágenes».
  - **Esto limita los E2E en Chromium headless en Linux.** Para cubrirlos, se debe aprobar una librería con versión exacta fijada en el lockfile y proveerla mediante el token `QR_IMAGE_ENGINE` (interfaz `QrImageEngine`), sin cambiar los componentes.
- **Rutas de estado y recibo, campo `payload`, cabecera `Idempotency-Key`, códigos y campos (P-1):** son supuestos. Hay que validarlos contra `design.md`, `spec.md` y el mock antes de dar el Issue por cumplido.
- **Importe (P-4):** sin conversión de unidad ni formato de moneda.
- **P-5, P-6, P-7 y P-8** siguen abiertos. El frontend no envía credenciales.
- **Eventos del mock:** se entregan manualmente. La UI no los presenta como webhooks ni como notificaciones automáticas.
- El importe de un pago recién creado en la pantalla de resultado se toma de lo enviado (o del QR fijo), no de la respuesta de W2.

---

# Código Angular

```typescript
// src/app/app.component.ts
import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="app-header">
      <nav aria-label="Principal">
        <a routerLink="/pagar-qr" routerLinkActive="active" ariaCurrentWhenActive="page">Pagar con QR</a>
        <a routerLink="/historial" routerLinkActive="active" ariaCurrentWhenActive="page">Historial de pagos QR</a>
      </nav>
    </header>
    <main id="contenido">
      <router-outlet />
    </main>
  `,
  styles: [
    `
      .app-header { padding: 0.75rem 1rem; border-bottom: 1px solid #c9ced6; }
      nav { display: flex; gap: 1.25rem; flex-wrap: wrap; }
      a { color: #0b4fa8; font-weight: 600; text-decoration: underline; padding: 0.25rem; }
      a.active { color: #111; text-decoration-thickness: 3px; }
      a:focus-visible { outline: 3px solid #1a73e8; outline-offset: 2px; }
      main { display: block; }
    `,
  ],
})
export class AppComponent {}
```

```typescript
// src/app/app.routes.ts
import { provideHttpClient } from '@angular/common/http';
import { Routes } from '@angular/router';

import { HistorialComponent } from './qr-pagos/historial.component';
import { PaymentHistoryService } from './qr-pagos/payment-history.service';
import { QrApiService } from './qr-pagos/qr-api.service';
import { QrDecoderService } from './qr-pagos/qr-decoder.service';
import { QrPagoComponent } from './qr-pagos/qr-pago.component';

export const routes: Routes = [
  {
    path: '',
    // Los servicios se proveen a nivel de ruta junto con HttpClient,
    // para no depender de la configuración global de main.ts.
    providers: [provideHttpClient(), QrApiService, QrDecoderService, PaymentHistoryService],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'pagar-qr' },
      { path: 'pagar-qr', component: QrPagoComponent, title: 'Pagar con QR' },
      { path: 'historial', component: HistorialComponent, title: 'Historial de pagos QR' },
    ],
  },
  { path: '**', redirectTo: 'pagar-qr' },
];
```

```typescript
// src/app/qr-pagos/qr-pagos.models.ts
export type AmountType = 'fixed' | 'open';

export interface QrResolveRequest {
  payload: string;
}

export interface QrResolveResponse {
  qrId: string;
  merchant: { name: string };
  amountType: AmountType;
  amount?: number | null;
  currency: string;
}

export interface PaymentRequest {
  qrId: string;
  amount: number;
  currency: string;
}

export interface PaymentResponse {
  paymentId: string;
  reference: string;
  status: string;
  qrId?: string;
}

export interface HistoryEntry {
  paymentId: string;
  reference: string;
  status: string;
  qrId: string;
  merchantName: string;
  amount: number;
  currency: string;
  /** Fecha ISO tomada del reloj de este dispositivo al registrar el pago (no la informa W2). */
  registeredAtLocal: string;
}

export interface HistoryStore {
  schemaVersion: 1;
  entries: HistoryEntry[];
}

/** Error normalizado de W2/W3 o de red. status 0 = sin conexión. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string | null,
    readonly serviceMessage: string | null,
  ) {
    super(code ?? `HTTP_${status}`);
  }
}
```

```typescript
// src/app/qr-pagos/qr-pagos.config.ts
import { InjectionToken } from '@angular/core';

/** Base de W3. Por defecto, mismo origen (p. ej. proxy hacia el mock). */
export const W3_BASE_URL = new InjectionToken<string>('W3_BASE_URL', {
  providedIn: 'root',
  factory: () => '',
});

/** Base de W2. Por defecto, mismo origen (p. ej. proxy hacia el mock). */
export const W2_BASE_URL = new InjectionToken<string>('W2_BASE_URL', {
  providedIn: 'root',
  factory: () => '',
});

// Rutas fijadas por el Issue.
export const W3_RESOLVE_PATH = '/qrs/resolve';
export const W2_PAYMENTS_PATH = '/payments';

// SUPUESTO (pendiente P-1): rutas de consulta de estado y recibo en W2.
export const w2PaymentStatusPath = (paymentId: string): string =>
  `/payments/${encodeURIComponent(paymentId)}`;
export const w2PaymentReceiptPath = (paymentId: string): string =>
  `/payments/${encodeURIComponent(paymentId)}/receipt`;

// SUPUESTO (pendiente P-1): nombre de la cabecera de idempotencia.
export const IDEMPOTENCY_HEADER = 'Idempotency-Key';
```

```typescript
// src/app/qr-pagos/qr-pagos.styles.ts
export const QR_STYLES = `
  :host { display: block; }
  .page { max-width: 52rem; margin: 0 auto; padding: 1rem; font-family: system-ui, sans-serif; line-height: 1.5; }
  h1 { font-size: 1.5rem; margin: 0.5rem 0 1rem; }
  h2 { font-size: 1.2rem; margin: 1.25rem 0 0.5rem; }
  section { margin-bottom: 1rem; }
  label { display: block; font-weight: 600; margin-bottom: 0.25rem; }
  input, select { font: inherit; padding: 0.4rem 0.5rem; border: 1px solid #5c6370; border-radius: 4px; max-width: 100%; }
  input[aria-invalid='true'] { border-color: #b00020; border-width: 2px; }
  button, .btn-link {
    font: inherit; padding: 0.5rem 0.9rem; border: 2px solid #0b4fa8; border-radius: 4px;
    background: #0b4fa8; color: #fff; cursor: pointer; text-decoration: none; display: inline-block; margin: 0 0.5rem 0.5rem 0;
  }
  button.secondary, .btn-link.secondary { background: #fff; color: #0b4fa8; }
  button:disabled { background: #e1e4e8; border-color: #8a919c; color: #4a505a; cursor: not-allowed; }
  :is(a, button, input, select, [tabindex]):focus-visible { outline: 3px solid #1a73e8; outline-offset: 2px; }
  [tabindex='-1']:focus { outline: 3px solid #1a73e8; outline-offset: 2px; }
  .hint { color: #38404b; font-size: 0.95rem; margin: 0.25rem 0 0.75rem; }
  .field-error { color: #b00020; font-weight: 600; margin: 0.25rem 0 0.75rem; }
  .alert { border: 2px solid #b00020; background: #fdecee; color: #4a0010; padding: 0.75rem 1rem; border-radius: 4px; margin: 1rem 0; }
  .alert h2 { margin-top: 0; font-size: 1.1rem; }
  .warn { border: 2px solid #8a6d00; background: #fff8dc; color: #3d3000; padding: 0.75rem 1rem; border-radius: 4px; margin: 1rem 0; }
  .ok { border: 2px solid #1b6e2d; background: #eaf6ec; padding: 0.75rem 1rem; border-radius: 4px; margin: 1rem 0; }
  .status { min-height: 1.5rem; font-weight: 600; }
  dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.25rem 1rem; margin: 0.5rem 0 1rem; }
  dt { font-weight: 600; }
  dd { margin: 0; overflow-wrap: anywhere; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #c9ced6; padding: 0.4rem 0.5rem; text-align: left; vertical-align: top; }
  th { background: #f1f3f6; }
  .filters { display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end; margin-bottom: 0.75rem; }
  .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
`;
```

```typescript
// src/app/qr-pagos/qr-decoder.service.ts
import { Injectable, InjectionToken, inject } from '@angular/core';

/**
 * Motor de lectura de QR sobre un bitmap. El motor por defecto usa la API nativa
 * BarcodeDetector (sin dependencias nuevas). Si el proyecto aprueba una librería
 * (P-3), se provee otro motor con este token sin cambiar los componentes.
 */
export interface QrImageEngine {
  readonly available: boolean;
  decode(image: ImageBitmap): Promise<string | null>;
}

interface BarcodeDetectorLike {
  detect(image: ImageBitmap): Promise<Array<{ rawValue?: string }>>;
}
type BarcodeDetectorCtor = new (options: { formats: string[] }) => BarcodeDetectorLike;

function createNativeEngine(): QrImageEngine {
  const ctor = (globalThis as unknown as { BarcodeDetector?: BarcodeDetectorCtor }).BarcodeDetector;
  return {
    available: typeof ctor === 'function',
    async decode(image: ImageBitmap): Promise<string | null> {
      if (!ctor) {
        return null;
      }
      const codes = await new ctor({ formats: ['qr_code'] }).detect(image);
      const found = codes.find((c) => typeof c.rawValue === 'string' && c.rawValue.length > 0);
      return found?.rawValue ?? null;
    },
  };
}

export const QR_IMAGE_ENGINE = new InjectionToken<QrImageEngine>('QR_IMAGE_ENGINE', {
  providedIn: 'root',
  factory: createNativeEngine,
});

export type QrDecodeReason = 'UNSUPPORTED' | 'NOT_IMAGE' | 'NO_QR' | 'READ_FAILED';

export class QrDecodeError extends Error {
  constructor(readonly reason: QrDecodeReason) {
    super(reason);
  }
}

@Injectable()
export class QrDecoderService {
  private readonly engine = inject(QR_IMAGE_ENGINE);

  /** Decodifica la imagen en el navegador y devuelve solo el texto del QR. */
  async decode(file: File): Promise<string> {
    if (!file.type.startsWith('image/')) {
      throw new QrDecodeError('NOT_IMAGE');
    }
    if (!this.engine.available) {
      throw new QrDecodeError('UNSUPPORTED');
    }

    let bitmap: ImageBitmap;
    try {
      bitmap = await createImageBitmap(file);
    } catch {
      throw new QrDecodeError('READ_FAILED');
    }

    try {
      const text = await this.engine.decode(bitmap);
      if (!text) {
        throw new QrDecodeError('NO_QR');
      }
      return text;
    } catch (error) {
      if (error instanceof QrDecodeError) {
        throw error;
      }
      throw new QrDecodeError('READ_FAILED');
    } finally {
      bitmap.close();
    }
  }
}
```

```typescript
// src/app/qr-pagos/qr-api.service.ts
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, map, throwError } from 'rxjs';

import {
  IDEMPOTENCY_HEADER,
  W2_BASE_URL,
  W2_PAYMENTS_PATH,
  W3_BASE_URL,
  W3_RESOLVE_PATH,
  w2PaymentReceiptPath,
  w2PaymentStatusPath,
} from './qr-pagos.config';
import {
  ApiError,
  PaymentRequest,
  PaymentResponse,
  QrResolveRequest,
  QrResolveResponse,
} from './qr-pagos.models';

/** Clave de idempotencia nueva (UUID si hay crypto.randomUUID; si no, 128 bits aleatorios en hex). */
export function newIdempotencyKey(): string {
  const c = globalThis.crypto;
  if (typeof c?.randomUUID === 'function') {
    return c.randomUUID();
  }
  const bytes = c.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }
  if (error instanceof HttpErrorResponse) {
    const body: unknown = error.error;
    let code: string | null = null;
    let message: string | null = null;
    if (body && typeof body === 'object') {
      const b = body as { code?: unknown; message?: unknown };
      code = typeof b.code === 'string' ? b.code : null;
      message = typeof b.message === 'string' ? b.message : null;
    }
    return new ApiError(error.status, code, message);
  }
  return new ApiError(0, null, null);
}

const invalidResponse = (): ApiError => new ApiError(200, 'RESPONSE_INVALID', null);

const isRecord = (v: unknown): v is Record<string, unknown> =>
  typeof v === 'object' && v !== null && !Array.isArray(v);

const isText = (v: unknown): v is string => typeof v === 'string' && v.length > 0;

@Injectable()
export class QrApiService {
  private readonly http = inject(HttpClient);
  private readonly w2 = inject(W2_BASE_URL);
  private readonly w3 = inject(W3_BASE_URL);

  /** W3 POST /qrs/resolve: envía solo el payload textual. */
  resolve(payload: string): Observable<QrResolveResponse> {
    const body: QrResolveRequest = { payload };
    return this.http.post<unknown>(`${this.w3}${W3_RESOLVE_PATH}`, body).pipe(
      map((r) => this.parseResolve(r)),
      catchError((e: unknown) => throwError(() => toApiError(e))),
    );
  }

  /** W2 POST /payments: conserva qrId y envía la clave de idempotencia. */
  createPayment(request: PaymentRequest, idempotencyKey: string): Observable<PaymentResponse> {
    const headers = new HttpHeaders({ [IDEMPOTENCY_HEADER]: idempotencyKey });
    return this.http.post<unknown>(`${this.w2}${W2_PAYMENTS_PATH}`, request, { headers }).pipe(
      map((r) => this.parsePayment(r)),
      catchError((e: unknown) => throwError(() => toApiError(e))),
    );
  }

  /** W2: consulta manual de estado (ruta supuesta, P-1). */
  getPayment(paymentId: string): Observable<{ status: string }> {
    return this.http.get<unknown>(`${this.w2}${w2PaymentStatusPath(paymentId)}`).pipe(
      map((r) => {
        if (!isRecord(r) || !isText(r['status'])) {
          throw invalidResponse();
        }
        return { status: r['status'] };
      }),
      catchError((e: unknown) => throwError(() => toApiError(e))),
    );
  }

  /** W2: consulta de recibo (ruta supuesta, P-1). Se devuelve tal cual. */
  getReceipt(paymentId: string): Observable<Record<string, unknown>> {
    return this.http.get<unknown>(`${this.w2}${w2PaymentReceiptPath(paymentId)}`).pipe(
      map((r) => {
        if (!isRecord(r)) {
          throw invalidResponse();
        }
        return r;
      }),
      catchError((e: unknown) => throwError(() => toApiError(e))),
    );
  }

  private parseResolve(r: unknown): QrResolveResponse {
    if (!isRecord(r) || !isText(r['qrId']) || !isText(r['currency'])) {
      throw invalidResponse();
    }
    const merchant = r['merchant'];
    if (!isRecord(merchant) || !isText(merchant['name'])) {
      throw invalidResponse();
    }
    const amountType = r['amountType'];
    if (amountType !== 'fixed' && amountType !== 'open') {
      throw invalidResponse();
    }
    const amount = r['amount'];
    return {
      qrId: r['qrId'],
      merchant: { name: merchant['name'] },
      amountType,
      amount: typeof amount === 'number' ? amount : null,
      currency: r['currency'],
    };
  }

  private parsePayment(r: unknown): PaymentResponse {
    if (!isRecord(r) || !isText(r['paymentId']) || !isText(r['reference']) || !isText(r['status'])) {
      throw invalidResponse();
    }
    return {
      paymentId: r['paymentId'],
      reference: r['reference'],
      status: r['status'],
      qrId: typeof r['qrId'] === 'string' ? r['qrId'] : undefined,
    };
  }
}
```

```typescript
// src/app/qr-pagos/error-messages.ts
import { QrDecodeError } from './qr-decoder.service';
import { ApiError } from './qr-pagos.models';

export type GuidanceAction = 'choose-another-qr' | 'revalidate' | 'none';
export type GuidanceContext = 'resolve' | 'payment' | 'status' | 'receipt';

export interface Guidance {
  title: string;
  detail: string;
  action: GuidanceAction;
  /** Mensaje textual devuelto por el servicio, si existe. */
  serviceMessage: string | null;
}

export function guidanceForDecode(error: QrDecodeError): Guidance {
  switch (error.reason) {
    case 'UNSUPPORTED':
      return {
        title: 'Tu navegador no puede leer QR desde imágenes',
        detail:
          'Prueba con un navegador compatible con BarcodeDetector (por ejemplo, Chrome en Android, macOS o ChromeOS). No se envió nada al servicio.',
        action: 'none',
        serviceMessage: null,
      };
    case 'NOT_IMAGE':
      return {
        title: 'El archivo no es una imagen',
        detail: 'Elige una imagen (PNG, JPG, etc.) que contenga el código QR del comercio.',
        action: 'choose-another-qr',
        serviceMessage: null,
      };
    case 'NO_QR':
      return {
        title: 'No se encontró un QR en la imagen',
        detail: 'Verifica que la imagen sea nítida y muestre el QR completo, o carga otra imagen.',
        action: 'choose-another-qr',
        serviceMessage: null,
      };
    default:
      return {
        title: 'No se pudo leer la imagen',
        detail: 'El archivo no se pudo procesar. Carga otra imagen.',
        action: 'choose-another-qr',
        serviceMessage: null,
      };
  }
}

export function guidanceFor(error: ApiError, context: GuidanceContext): Guidance {
  const serviceMessage = error.serviceMessage;
  const make = (title: string, detail: string, action: GuidanceAction = 'none'): Guidance => ({
    title,
    detail,
    action,
    serviceMessage,
  });

  switch (error.code) {
    case 'QR_INVALID':
      return make(
        'El código QR no es válido',
        'No se pudo validar el contenido de la imagen. Verifica que sea el QR completo del comercio o carga otra imagen.',
        'choose-another-qr',
      );
    case 'QR_UNKNOWN':
      return make(
        'QR no reconocido',
        'Este QR no corresponde a un comercio conocido. Confirma con el comercio que sea su QR de pago.',
        'choose-another-qr',
      );
    case 'QR_EXPIRED':
      return make(
        'El QR expiró',
        'Pide al comercio un QR vigente y cárgalo. La respuesta indica que el pago no se realizó.',
        'choose-another-qr',
      );
    case 'QR_CONFLICT':
      return make(
        'Los datos del comercio o del importe cambiaron',
        'Hay un conflicto entre el QR y el pago. No confirmes con los datos anteriores: vuelve a validar el QR para ver los datos actuales.',
        'revalidate',
      );
    case 'AMOUNT_INVALID':
      return make('Importe no válido', 'Ingresa un importe mayor que 0 y vuelve a confirmar.');
    case 'IDEMPOTENCY_CONFLICT':
      return make(
        'Solicitud repetida con datos distintos',
        'Se generará una solicitud nueva. Revisa los datos y confirma de nuevo.',
      );
    case 'PAYLOAD_TOO_LARGE':
      return make(
        'El contenido del QR es demasiado grande',
        'El servicio rechazó el contenido. Elige otro QR.',
        'choose-another-qr',
      );
    case 'RESPONSE_INVALID':
      return make(
        'Respuesta inesperada del servicio',
        'El servicio devolvió datos que no cumplen el contrato esperado. No se muestra ningún pago como creado; revisa el historial o inténtalo más tarde.',
      );
    default:
      break;
  }

  if (error.status === 413) {
    return make(
      'El contenido del QR es demasiado grande',
      'El servicio rechazó el contenido. Elige otro QR.',
      'choose-another-qr',
    );
  }
  if (error.status === 401 || error.status === 403) {
    return make('No tienes autorización', 'El servicio rechazó la solicitud por falta de autorización.');
  }
  if (error.status === 404 && (context === 'status' || context === 'receipt')) {
    return make(
      'No se encontró el pago o el recibo',
      'El servicio no tiene información para este pago todavía. Inténtalo más tarde.',
    );
  }
  if (error.status === 0) {
    return make(
      'Sin conexión con el servicio',
      context === 'payment'
        ? 'No se pudo contactar al servicio. Verifica tu conexión y vuelve a pulsar «Confirmar pago»: se reutiliza la misma solicitud, así se evita un cobro duplicado.'
        : 'No se pudo contactar al servicio. Verifica tu conexión o que el servicio esté disponible e inténtalo de nuevo.',
    );
  }
  if (error.status >= 500) {
    return make(
      'El servicio no pudo procesar la solicitud',
      context === 'payment'
        ? 'Inténtalo de nuevo. Si repites «Confirmar pago», se reutiliza la misma solicitud.'
        : 'Inténtalo de nuevo en unos minutos.',
    );
  }
  return make(
    'No se pudo completar la operación',
    serviceMessage ?? `El servicio respondió con el código ${error.code ?? error.status}.`,
  );
}
```

```typescript
// src/app/qr-pagos/payment-history.service.ts
import { Injectable, OnDestroy, signal } from '@angular/core';

import { HistoryEntry, HistoryStore } from './qr-pagos.models';

const STORAGE_KEY = 'merchantQrPayments.history';
const SCHEMA_VERSION = 1;

interface ReadResult {
  entries: HistoryEntry[];
  /** false si la clave tiene un formato ajeno: no se sobrescribe. */
  compatible: boolean;
}

function isEntry(v: unknown): v is HistoryEntry {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const e = v as Record<string, unknown>;
  return (
    typeof e['paymentId'] === 'string' &&
    typeof e['reference'] === 'string' &&
    typeof e['status'] === 'string' &&
    typeof e['qrId'] === 'string' &&
    typeof e['merchantName'] === 'string' &&
    typeof e['amount'] === 'number' &&
    typeof e['currency'] === 'string' &&
    typeof e['registeredAtLocal'] === 'string' &&
    !Number.isNaN(Date.parse(e['registeredAtLocal']))
  );
}

/** Historial local de pagos iniciados por este flujo. Solo escribe pagos creados por POST /payments. */
@Injectable()
export class PaymentHistoryService implements OnDestroy {
  private readonly _entries = signal<HistoryEntry[]>(this.read().entries);
  readonly entries = this._entries.asReadonly();

  private readonly onStorage = (event: StorageEvent): void => {
    if (event.key === null || event.key === STORAGE_KEY) {
      this._entries.set(this.read().entries);
    }
  };

  constructor() {
    window.addEventListener('storage', this.onStorage);
  }

  ngOnDestroy(): void {
    window.removeEventListener('storage', this.onStorage);
  }

  /** Devuelve false si no se pudo guardar (formato ajeno, cuota o almacenamiento no disponible). */
  add(entry: HistoryEntry): boolean {
    const current = this.read();
    if (!current.compatible) {
      return false;
    }
    const rest = current.entries.filter((e) => e.paymentId !== entry.paymentId);
    return this.write([entry, ...rest]);
  }

  update(paymentId: string, patch: Partial<Pick<HistoryEntry, 'status'>>): boolean {
    const current = this.read();
    if (!current.compatible) {
      return false;
    }
    const next = current.entries.map((e) => (e.paymentId === paymentId ? { ...e, ...patch } : e));
    return this.write(next);
  }

  private write(entries: HistoryEntry[]): boolean {
    const store: HistoryStore = { schemaVersion: SCHEMA_VERSION, entries };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
    } catch {
      return false;
    }
    this._entries.set(entries);
    return true;
  }

  private read(): ReadResult {
    let raw: string | null;
    try {
      raw = localStorage.getItem(STORAGE_KEY);
    } catch {
      return { entries: [], compatible: false };
    }
    if (raw === null) {
      return { entries: [], compatible: true };
    }
    try {
      const parsed: unknown = JSON.parse(raw);
      if (
        typeof parsed === 'object' &&
        parsed !== null &&
        (parsed as { schemaVersion?: unknown }).schemaVersion === SCHEMA_VERSION &&
        Array.isArray((parsed as { entries?: unknown }).entries)
      ) {
        const entries = (parsed as { entries: unknown[] }).entries.filter(isEntry);
        return { entries, compatible: true };
      }
    } catch {
      // JSON corrupto: se ignora sin romper la pantalla.
    }
    return { entries: [], compatible: false };
  }
}
```

```typescript
// src/app/qr-pagos/qr-pago.component.ts
import { Component, ElementRef, ViewChild, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  AbstractControl,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
} from '@angular/forms';
import { RouterLink } from '@angular/router';

import { Guidance, guidanceFor, guidanceForDecode } from './error-messages';
import { PaymentHistoryService } from './payment-history.service';
import { QrApiService, newIdempotencyKey, toApiError } from './qr-api.service';
import { QrDecodeError, QrDecoderService } from './qr-decoder.service';
import { PaymentResponse, QrResolveResponse } from './qr-pagos.models';
import { QR_STYLES } from './qr-pagos.styles';

type Phase = 'idle' | 'decoding' | 'resolving' | 'review' | 'submitting' | 'success';

interface Attempt {
  key: string;
  qrId: string;
  amount: number;
  currency: string;
}

function positiveAmount(control: AbstractControl): ValidationErrors | null {
  const v: unknown = control.value;
  return typeof v === 'number' && Number.isFinite(v) && v > 0 ? null : { positive: true };
}

@Component({
  selector: 'app-qr-pago',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './qr-pago.component.html',
  styles: [QR_STYLES],
})
export class QrPagoComponent {
  private readonly decoder = inject(QrDecoderService);
  private readonly api = inject(QrApiService);
  private readonly history = inject(PaymentHistoryService);

  @ViewChild('fileInput') fileInput?: ElementRef<HTMLInputElement>;
  @ViewChild('alertBox') alertBox?: ElementRef<HTMLElement>;
  @ViewChild('reviewHeading') reviewHeading?: ElementRef<HTMLElement>;
  @ViewChild('successHeading') successHeading?: ElementRef<HTMLElement>;

  readonly phase = signal<Phase>('idle');
  readonly resolved = signal<QrResolveResponse | null>(null);
  readonly payment = signal<PaymentResponse | null>(null);
  readonly paidAmount = signal<{ amount: number; currency: string } | null>(null);
  readonly error = signal<Guidance | null>(null);
  readonly historyWarning = signal(false);
  readonly refreshing = signal(false);
  readonly statusNote = signal<string | null>(null);

  readonly amountCtrl = new FormControl<number | null>(null, [positiveAmount]);
  readonly form = new FormGroup({ amount: this.amountCtrl });
  private readonly amountValue = toSignal(this.amountCtrl.valueChanges, {
    initialValue: this.amountCtrl.value,
  });

  /** Importe a enviar: el del QR fijo o el digitado en monto abierto. null si no es válido. */
  readonly amountToPay = computed<number | null>(() => {
    const qr = this.resolved();
    if (!qr) {
      return null;
    }
    const v = qr.amountType === 'fixed' ? qr.amount : this.amountValue();
    return typeof v === 'number' && Number.isFinite(v) && v > 0 ? v : null;
  });

  readonly busy = computed(() => {
    const p = this.phase();
    return p === 'decoding' || p === 'resolving' || p === 'submitting';
  });

  readonly canConfirm = computed(() => this.phase() === 'review' && this.amountToPay() !== null);

  private lastPayload: string | null = null;
  private attempt: Attempt | null = null;

  async onFileSelected(event: Event): Promise<void> {
    if (this.busy()) {
      return;
    }
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }
    input.value = ''; // permite volver a elegir el mismo archivo
    this.resetFlow();
    this.phase.set('decoding');
    try {
      this.lastPayload = await this.decoder.decode(file);
    } catch (e) {
      this.phase.set('idle');
      this.showError(guidanceForDecode(e instanceof QrDecodeError ? e : new QrDecodeError('READ_FAILED')));
      return;
    }
    this.resolve(this.lastPayload);
  }

  revalidate(): void {
    if (this.busy() || !this.lastPayload) {
      return;
    }
    this.resolve(this.lastPayload);
  }

  confirm(): void {
    const qr = this.resolved();
    const amount = this.amountToPay();
    if (this.phase() !== 'review' || !qr) {
      return; // evita envíos duplicados
    }
    if (amount === null) {
      this.amountCtrl.markAsTouched();
      return;
    }

    // Reutiliza la clave solo si es el mismo intento (mismo QR, importe y moneda).
    const same =
      this.attempt !== null &&
      this.attempt.qrId === qr.qrId &&
      this.attempt.amount === amount &&
      this.attempt.currency === qr.currency;
    const attempt: Attempt = same
      ? (this.attempt as Attempt)
      : { key: newIdempotencyKey(), qrId: qr.qrId, amount, currency: qr.currency };
    this.attempt = attempt;

    this.error.set(null);
    this.phase.set('submitting'); // síncrono: bloquea clics repetidos

    this.api
      .createPayment({ qrId: qr.qrId, amount, currency: qr.currency }, attempt.key)
      .subscribe({
        next: (p) => {
          this.attempt = null;
          this.payment.set(p);
          this.paidAmount.set({ amount, currency: qr.currency });
          const saved = this.history.add({
            paymentId: p.paymentId,
            reference: p.reference,
            status: p.status,
            qrId: qr.qrId,
            merchantName: qr.merchant.name,
            amount,
            currency: qr.currency,
            registeredAtLocal: new Date().toISOString(),
          });
          this.historyWarning.set(!saved);
          this.phase.set('success');
          this.focus(() => this.successHeading);
        },
        error: (e: unknown) => {
          const err = toApiError(e);
          const guidance = guidanceFor(err, 'payment');
          if (err.code === 'IDEMPOTENCY_CONFLICT') {
            this.attempt = null;
          }
          if (guidance.action === 'revalidate' || guidance.action === 'choose-another-qr') {
            // La revisión ya no es confiable: se descarta para no confirmar con datos previos.
            this.attempt = null;
            this.resolved.set(null);
            this.amountCtrl.reset();
            this.phase.set('idle');
          } else {
            this.phase.set('review');
          }
          this.showError(guidance);
        },
      });
  }

  /** Consulta manual a W2: los eventos del mock no llegan solos. */
  refreshStatus(): void {
    const p = this.payment();
    if (!p || this.refreshing()) {
      return;
    }
    this.refreshing.set(true);
    this.error.set(null);
    this.statusNote.set(null);
    this.api.getPayment(p.paymentId).subscribe({
      next: (r) => {
        this.payment.set({ ...p, status: r.status });
        this.history.update(p.paymentId, { status: r.status });
        this.statusNote.set(`Estado consultado a W2: ${r.status}.`);
        this.refreshing.set(false);
      },
      error: (e: unknown) => {
        this.refreshing.set(false);
        this.showError(guidanceFor(toApiError(e), 'status'));
      },
    });
  }

  chooseAnother(): void {
    this.error.set(null);
    this.fileInput?.nativeElement.focus();
  }

  startOver(): void {
    this.resetFlow();
    this.lastPayload = null;
    this.focus(() => this.fileInput);
  }

  amountError(): string | null {
    const c = this.amountCtrl;
    if (c.value === null) {
      return c.touched ? 'Ingresa el importe a pagar.' : null;
    }
    return c.valid ? null : 'El importe debe ser un número mayor que 0.';
  }

  private resolve(payload: string): void {
    this.error.set(null);
    this.resolved.set(null);
    this.attempt = null;
    this.amountCtrl.reset();
    this.phase.set('resolving');
    this.api.resolve(payload).subscribe({
      next: (qr) => {
        this.resolved.set(qr);
        this.phase.set('review');
        this.focus(() => this.reviewHeading);
      },
      error: (e: unknown) => {
        this.phase.set('idle');
        this.showError(guidanceFor(toApiError(e), 'resolve'));
      },
    });
  }

  private resetFlow(): void {
    this.phase.set('idle');
    this.resolved.set(null);
    this.payment.set(null);
    this.paidAmount.set(null);
    this.error.set(null);
    this.historyWarning.set(false);
    this.statusNote.set(null);
    this.attempt = null;
    this.amountCtrl.reset();
  }

  private showError(guidance: Guidance): void {
    this.error.set(guidance);
    this.focus(() => this.alertBox);
  }

  private focus(target: () => ElementRef<HTMLElement> | undefined): void {
    setTimeout(() => target()?.nativeElement.focus(), 0);
  }
}
```

```html
<!-- src/app/qr-pagos/qr-pago.component.html -->
<div class="page">
  <h1>Pagar con QR de comercio</h1>
  <p class="hint">
    Carga la imagen del QR del comercio, revisa el comercio y el importe, y confirma el pago.
    La imagen se lee en tu navegador y solo se envía el texto del QR.
  </p>

  <section aria-labelledby="paso-1">
    <h2 id="paso-1">1. Cargar la imagen del QR</h2>
    <label for="qr-file">Imagen del código QR</label>
    <input
      #fileInput
      id="qr-file"
      type="file"
      accept="image/*"
      aria-describedby="qr-file-help"
      [disabled]="busy()"
      (change)="onFileSelected($event)"
    />
    <p id="qr-file-help" class="hint">Formatos de imagen habituales (PNG, JPG…).</p>
  </section>

  <div class="status" role="status" aria-live="polite">
    @switch (phase()) {
      @case ('decoding') { Leyendo la imagen… }
      @case ('resolving') { Validando el QR… }
      @case ('submitting') { Confirmando pago… }
    }
  </div>

  @if (error(); as g) {
    <div #alertBox class="alert" role="alert" tabindex="-1">
      <h2>{{ g.title }}</h2>
      <p>{{ g.detail }}</p>
      @if (g.serviceMessage) {
        <p><strong>Detalle del servicio:</strong> {{ g.serviceMessage }}</p>
      }
      @if (g.action === 'choose-another-qr') {
        <button type="button" (click)="chooseAnother()">Ir a cargar otra imagen</button>
      }
      @if (g.action === 'revalidate') {
        <button type="button" [disabled]="busy()" (click)="revalidate()">Volver a validar el QR</button>
      }
    </div>
  }

  @if (resolved(); as qr) {
    @if (phase() !== 'success') {
      <section aria-labelledby="paso-2">
        <h2 #reviewHeading id="paso-2" tabindex="-1">2. Revisa y confirma</h2>
        <dl>
          <dt>Comercio</dt>
          <dd>{{ qr.merchant.name }}</dd>
          <dt>Tipo de importe</dt>
          <dd>{{ qr.amountType === 'fixed' ? 'Importe fijo' : 'Monto abierto (lo defines tú)' }}</dd>
          @if (qr.amountType === 'fixed') {
            <dt>Importe</dt>
            <dd>{{ qr.amount }} {{ qr.currency }}</dd>
          }
        </dl>

        <form [formGroup]="form" (ngSubmit)="confirm()" novalidate>
          @if (qr.amountType === 'open') {
            <label for="amount">Importe a pagar ({{ qr.currency }})</label>
            <input
              id="amount"
              type="number"
              inputmode="decimal"
              step="any"
              min="0"
              required
              formControlName="amount"
              aria-describedby="amount-help amount-error"
              [attr.aria-invalid]="amountError() ? 'true' : null"
            />
            <p id="amount-help" class="hint">Este QR no trae importe. Debe ser un número mayor que 0.</p>
            <p id="amount-error" class="field-error" role="alert">{{ amountError() }}</p>
          } @else if (amountToPay() === null) {
            <p class="field-error" role="alert">El QR trae un importe no válido; no se puede confirmar.</p>
          }

          <button type="submit" [disabled]="!canConfirm()" [attr.aria-busy]="phase() === 'submitting'">
            {{ phase() === 'submitting' ? 'Confirmando pago…' : 'Confirmar pago' }}
          </button>
        </form>
      </section>
    }
  }

  @if (phase() === 'success' && payment(); as p) {
    <section class="ok" aria-labelledby="exito">
      <h2 #successHeading id="exito" tabindex="-1">Pago creado</h2>
      <dl>
        @if (resolved(); as qr) {
          <dt>Comercio</dt>
          <dd>{{ qr.merchant.name }}</dd>
        }
        @if (paidAmount(); as pa) {
          <dt>Importe</dt>
          <dd>{{ pa.amount }} {{ pa.currency }}</dd>
        }
        <dt>Referencia</dt>
        <dd>{{ p.reference }}</dd>
        <dt>ID de pago</dt>
        <dd>{{ p.paymentId }}</dd>
        <dt>Estado</dt>
        <dd>{{ p.status }}</dd>
      </dl>
      <p class="hint">
        El estado no cambia solo: los eventos del mock se entregan manualmente. Usa «Actualizar estado» para consultarlo.
      </p>
      <div class="status" role="status" aria-live="polite">
        @if (refreshing()) { Consultando estado… } @else if (statusNote()) { {{ statusNote() }} }
      </div>
      <button type="button" [disabled]="refreshing()" (click)="refreshStatus()">Actualizar estado</button>
      <a class="btn-link secondary" routerLink="/historial">Ver historial</a>
      <button type="button" class="secondary" (click)="startOver()">Pagar otro QR</button>
    </section>

    @if (historyWarning()) {
      <div class="warn" role="status">
        El pago se creó, pero no se pudo guardar en el historial local de este navegador.
        Anota la referencia {{ p.reference }}.
      </div>
    }
  }
</div>
```

```typescript
// src/app/qr-pagos/historial.component.ts
import { DatePipe } from '@angular/common';
import { Component, ElementRef, ViewChild, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Guidance, guidanceFor } from './error-messages';
import { PaymentHistoryService } from './payment-history.service';
import { QrApiService, toApiError } from './qr-api.service';
import { HistoryEntry } from './qr-pagos.models';
import { QR_STYLES } from './qr-pagos.styles';

interface ReceiptView {
  reference: string;
  fields: Array<{ label: string; value: string }>;
}

@Component({
  selector: 'app-historial',
  standalone: true,
  imports: [DatePipe, RouterLink],
  templateUrl: './historial.component.html',
  styles: [QR_STYLES],
})
export class HistorialComponent {
  private readonly history = inject(PaymentHistoryService);
  private readonly api = inject(QrApiService);

  @ViewChild('alertBox') alertBox?: ElementRef<HTMLElement>;
  @ViewChild('receiptBox') receiptBox?: ElementRef<HTMLElement>;

  readonly entries = this.history.entries;
  readonly query = signal('');
  readonly statusFilter = signal('');
  readonly busyKey = signal<string | null>(null);
  readonly busyText = signal('');
  readonly error = signal<Guidance | null>(null);
  readonly receipt = signal<ReceiptView | null>(null);
  readonly note = signal<string | null>(null);

  readonly statuses = computed(() =>
    Array.from(new Set(this.entries().map((e) => e.status))).sort(),
  );

  /** Filtro 100 % local: no hay llamadas de red. */
  readonly filtered = computed(() => {
    const q = this.query().trim().toLowerCase();
    const s = this.statusFilter();
    return this.entries().filter(
      (e) =>
        (!s || e.status === s) &&
        (!q || [e.reference, e.merchantName, e.paymentId].some((x) => x.toLowerCase().includes(q))),
    );
  });

  onQuery(event: Event): void {
    this.query.set((event.target as HTMLInputElement).value);
  }

  onStatus(event: Event): void {
    this.statusFilter.set((event.target as HTMLSelectElement).value);
  }

  clearFilters(): void {
    this.query.set('');
    this.statusFilter.set('');
  }

  /** Consulta manual a W2: sin polling ni simulación de webhooks. */
  refresh(entry: HistoryEntry): void {
    if (this.busyKey() !== null) {
      return;
    }
    this.busyKey.set(entry.paymentId);
    this.busyText.set('Consultando estado…');
    this.error.set(null);
    this.note.set(null);
    this.api.getPayment(entry.paymentId).subscribe({
      next: (r) => {
        this.history.update(entry.paymentId, { status: r.status });
        this.note.set(`Pago ${entry.reference}: estado consultado a W2 = ${r.status}.`);
        this.busyKey.set(null);
      },
      error: (e: unknown) => {
        this.busyKey.set(null);
        this.showError(guidanceFor(toApiError(e), 'status'));
      },
    });
  }

  viewReceipt(entry: HistoryEntry): void {
    if (this.busyKey() !== null) {
      return;
    }
    this.busyKey.set(entry.paymentId);
    this.busyText.set('Consultando recibo…');
    this.error.set(null);
    this.note.set(null);
    this.api.getReceipt(entry.paymentId).subscribe({
      next: (r) => {
        this.receipt.set({
          reference: entry.reference,
          fields: Object.entries(r).map(([label, v]) => ({
            label,
            value: typeof v === 'object' && v !== null ? JSON.stringify(v) : String(v ?? ''),
          })),
        });
        this.busyKey.set(null);
        setTimeout(() => this.receiptBox?.nativeElement.focus(), 0);
      },
      error: (e: unknown) => {
        this.busyKey.set(null);
        this.showError(guidanceFor(toApiError(e), 'receipt'));
      },
    });
  }

  closeReceipt(): void {
    this.receipt.set(null);
  }

  private showError(guidance: Guidance): void {
    this.error.set(guidance);
    setTimeout(() => this.alertBox?.nativeElement.focus(), 0);
  }
}
```

```html
<!-- src/app/qr-pagos/historial.component.html -->
<div class="page">
  <h1>Historial de pagos QR</h1>
  <p class="hint">
    Solo se listan los pagos iniciados desde esta aplicación en este navegador. Los filtros se aplican localmente.
    Los eventos del mock se entregan manualmente: el estado solo cambia cuando pulsas «Actualizar estado».
  </p>

  <div class="status" role="status" aria-live="polite">
    @if (busyKey() !== null) {
      {{ busyText() }}
    } @else if (note()) {
      {{ note() }}
    }
  </div>

  @if (error(); as g) {
    <div #alertBox class="alert" role="alert" tabindex="-1">
      <h2>{{ g.title }}</h2>
      <p>{{ g.detail }}</p>
      @if (g.serviceMessage) {
        <p><strong>Detalle del servicio:</strong> {{ g.serviceMessage }}</p>
      }
    </div>
  }

  @if (entries().length === 0) {
    <section aria-labelledby="vacio">
      <h2 id="vacio">Aún no hay pagos QR iniciados desde esta aplicación</h2>
      <p>Cuando confirmes un pago con QR aparecerá aquí.</p>
      <a class="btn-link" routerLink="/pagar-qr">Pagar con QR</a>
    </section>
  } @else {
    <form class="filters" (submit)="$event.preventDefault()" role="search" aria-label="Filtrar historial">
      <div>
        <label for="f-query">Buscar por referencia, comercio o ID de pago</label>
        <input id="f-query" type="search" [value]="query()" (input)="onQuery($event)" />
      </div>
      <div>
        <label for="f-status">Estado</label>
        <select id="f-status" (change)="onStatus($event)">
          <option value="" [selected]="statusFilter() === ''">Todos</option>
          @for (s of statuses(); track s) {
            <option [value]="s" [selected]="statusFilter() === s">{{ s }}</option>
          }
        </select>
      </div>
      <button type="button" class="secondary" (click)="clearFilters()">Limpiar filtros</button>
    </form>

    <p role="status" aria-live="polite">Mostrando {{ filtered().length }} de {{ entries().length }} pagos.</p>

    @if (filtered().length === 0) {
      <p>Ningún pago coincide con el filtro.</p>
    } @else {
      <table>
        <caption class="sr-only">Pagos QR iniciados desde esta aplicación</caption>
        <thead>
          <tr>
            <th scope="col">Comercio</th>
            <th scope="col">Referencia</th>
            <th scope="col">Importe</th>
            <th scope="col">Estado</th>
            <th scope="col">Fecha local registrada</th>
            <th scope="col">Acciones</th>
          </tr>
        </thead>
        <tbody>
          @for (e of filtered(); track e.paymentId) {
            <tr>
              <td>{{ e.merchantName }}</td>
              <td>{{ e.reference }}</td>
              <td>{{ e.amount }} {{ e.currency }}</td>
              <td>{{ e.status }}</td>
              <td>
                <time [attr.datetime]="e.registeredAtLocal">{{ e.registeredAtLocal | date: 'dd/MM/yyyy HH:mm:ss' }}</time>
                <span class="hint"> (hora de este dispositivo)</span>
              </td>
              <td>
                <button
                  type="button"
                  [disabled]="busyKey() !== null"
                  [attr.aria-label]="'Actualizar estado del pago ' + e.reference"
                  (click)="refresh(e)"
                >
                  Actualizar estado
                </button>
                <button
                  type="button"
                  class="secondary"
                  [disabled]="busyKey() !== null"
                  [attr.aria-label]="'Ver recibo del pago ' + e.reference"
                  (click)="viewReceipt(e)"
                >
                  Ver recibo
                </button>
              </td>
            </tr>
          }
        </tbody>
      </table>
    }
  }

  @if (receipt(); as r) {
    <section #receiptBox class="ok" aria-labelledby="recibo-titulo" tabindex="-1">
      <h2 id="recibo-titulo">Recibo del pago {{ r.reference }}</h2>
      @if (r.fields.length === 0) {
        <p>El servicio devolvió un recibo sin campos.</p>
      } @else {
        <dl>
          @for (f of r.fields; track f.label) {
            <dt>{{ f.label }}</dt>
            <dd>{{ f.value }}</dd>
          }
        </dl>
      }
      <button type="button" class="secondary" (click)="closeReceipt()">Cerrar recibo</button>
    </section>
  }
</div>
```