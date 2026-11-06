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
