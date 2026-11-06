// src/app/qr-pagos/payment-history.service.spec.ts
import { TestBed } from '@angular/core/testing';

import { PaymentHistoryService } from './payment-history.service';
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

describe('PaymentHistoryService (H03 CA-5)', () => {
  function create(): PaymentHistoryService {
    TestBed.configureTestingModule({ providers: [PaymentHistoryService] });
    return TestBed.inject(PaymentHistoryService);
  }

  beforeEach(() => localStorage.removeItem(KEY));
  afterEach(() => localStorage.removeItem(KEY));

  it('FE-STO-01 add guarda con schemaVersion 1 y la fecha local registrada', () => {
    const svc = create();
    expect(svc.add(entry('pay_1'))).toBeTrue();
    const stored = JSON.parse(localStorage.getItem(KEY) as string);
    expect(stored.schemaVersion).toBe(1);
    expect(stored.entries.length).toBe(1);
    expect(stored.entries[0].registeredAtLocal).toBe('2026-11-06T10:00:00.000Z');
    expect(svc.entries().map((e) => e.paymentId)).toEqual(['pay_1']);
  });

  it('FE-STO-02 deduplica por paymentId y deja la entrada más reciente primero', () => {
    const svc = create();
    svc.add(entry('pay_1'));
    svc.add(entry('pay_2'));
    svc.add(entry('pay_1', { status: 'completed' }));
    expect(svc.entries().map((e) => e.paymentId)).toEqual(['pay_1', 'pay_2']);
    expect(svc.entries()[0].status).toBe('completed');
  });

  it('FE-STO-03 ignora entradas corruptas sin romper la lectura', () => {
    localStorage.setItem(
      KEY,
      JSON.stringify({
        schemaVersion: 1,
        entries: [entry('pay_ok'), { paymentId: 1 }, null, 'texto', entry('pay_fecha', { registeredAtLocal: 'no-fecha' })],
      }),
    );
    const svc = create();
    expect(svc.entries().map((e) => e.paymentId)).toEqual(['pay_ok']);
  });

  it('FE-STO-04 con JSON ilegible no sobrescribe y add devuelve false', () => {
    localStorage.setItem(KEY, '{basura');
    const svc = create();
    expect(svc.entries()).toEqual([]);
    expect(svc.add(entry('pay_1'))).toBeFalse();
    expect(localStorage.getItem(KEY)).toBe('{basura');
  });

  it('FE-STO-05 con un esquema ajeno no sobrescribe los datos', () => {
    const foreign = JSON.stringify({ schemaVersion: 2, entries: [{ otro: true }] });
    localStorage.setItem(KEY, foreign);
    const svc = create();
    expect(svc.add(entry('pay_1'))).toBeFalse();
    expect(svc.update('pay_1', { status: 'x' })).toBeFalse();
    expect(localStorage.getItem(KEY)).toBe(foreign);
  });

  it('FE-STO-06 el evento storage de la clave refresca la lista (otra pestaña)', () => {
    const svc = create();
    expect(svc.entries()).toEqual([]);
    localStorage.setItem(KEY, JSON.stringify({ schemaVersion: 1, entries: [entry('pay_otra_pestana')] }));
    window.dispatchEvent(new StorageEvent('storage', { key: KEY }));
    expect(svc.entries().map((e) => e.paymentId)).toEqual(['pay_otra_pestana']);
  });

  it('FE-STO-07 el evento storage de otra clave no refresca la lista', () => {
    const svc = create();
    localStorage.setItem(KEY, JSON.stringify({ schemaVersion: 1, entries: [entry('pay_1')] }));
    window.dispatchEvent(new StorageEvent('storage', { key: 'otra.clave' }));
    expect(svc.entries()).toEqual([]);
  });

  it('FE-STO-08 si el almacenamiento falla (cuota) add devuelve false y no cambia la lista', () => {
    const svc = create();
    spyOn(Storage.prototype, 'setItem').and.throwError('QuotaExceededError');
    expect(svc.add(entry('pay_1'))).toBeFalse();
    expect(svc.entries()).toEqual([]);
  });

  it('FE-STO-09 update cambia solo el estado de la entrada indicada', () => {
    const svc = create();
    svc.add(entry('pay_1'));
    svc.add(entry('pay_2'));
    expect(svc.update('pay_1', { status: 'completed' })).toBeTrue();
    const byId = Object.fromEntries(svc.entries().map((e) => [e.paymentId, e]));
    expect(byId['pay_1'].status).toBe('completed');
    expect(byId['pay_1'].registeredAtLocal).toBe('2026-11-06T10:00:00.000Z');
    expect(byId['pay_2'].status).toBe('pending');
  });
});
