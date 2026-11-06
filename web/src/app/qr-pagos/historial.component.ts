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
