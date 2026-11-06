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
