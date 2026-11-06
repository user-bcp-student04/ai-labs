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
