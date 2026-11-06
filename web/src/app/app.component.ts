// src/app/app.component.ts
import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="app-header">
      <nav aria-label="Principal">
        <a routerLink="/pagar-qr" routerLinkActive="active" ariaCurrentWhenActive="page">Pagar con QR</a>
        <a routerLink="/historial" routerLinkActive="active" ariaCurrentWhenActive="page">Historial de pagos QR</a>
      </nav>
    </header>
    <main id="contenido">
      <router-outlet />
    </main>
  `,
  styles: [
    `
      .app-header { padding: 0.75rem 1rem; border-bottom: 1px solid #c9ced6; }
      nav { display: flex; gap: 1.25rem; flex-wrap: wrap; }
      a { color: #0b4fa8; font-weight: 600; text-decoration: underline; padding: 0.25rem; }
      a.active { color: #111; text-decoration-thickness: 3px; }
      a:focus-visible { outline: 3px solid #1a73e8; outline-offset: 2px; }
      main { display: block; }
    `,
  ],
})
export class AppComponent {}
