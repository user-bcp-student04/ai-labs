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
