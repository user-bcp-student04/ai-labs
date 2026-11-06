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
