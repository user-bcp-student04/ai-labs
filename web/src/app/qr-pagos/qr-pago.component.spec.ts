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
