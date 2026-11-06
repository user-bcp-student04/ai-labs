// src/app/app.routes.ts
import { provideHttpClient } from '@angular/common/http';
import { Routes } from '@angular/router';

import { HistorialComponent } from './qr-pagos/historial.component';
import { PaymentHistoryService } from './qr-pagos/payment-history.service';
import { QrApiService } from './qr-pagos/qr-api.service';
import { QrDecoderService } from './qr-pagos/qr-decoder.service';
import { QrPagoComponent } from './qr-pagos/qr-pago.component';

export const routes: Routes = [
  {
    path: '',
    // Los servicios se proveen a nivel de ruta junto con HttpClient,
    // para no depender de la configuración global de main.ts.
    providers: [provideHttpClient(), QrApiService, QrDecoderService, PaymentHistoryService],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'pagar-qr' },
      { path: 'pagar-qr', component: QrPagoComponent, title: 'Pagar con QR' },
      { path: 'historial', component: HistorialComponent, title: 'Historial de pagos QR' },
    ],
  },
  { path: '**', redirectTo: 'pagar-qr' },
];
