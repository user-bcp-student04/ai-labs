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
