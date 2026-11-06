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
