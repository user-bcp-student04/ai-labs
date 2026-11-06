// src/app/qr-pagos/qr-pagos.styles.ts
export const QR_STYLES = `
  :host { display: block; }
  .page { max-width: 52rem; margin: 0 auto; padding: 1rem; font-family: system-ui, sans-serif; line-height: 1.5; }
  h1 { font-size: 1.5rem; margin: 0.5rem 0 1rem; }
  h2 { font-size: 1.2rem; margin: 1.25rem 0 0.5rem; }
  section { margin-bottom: 1rem; }
  label { display: block; font-weight: 600; margin-bottom: 0.25rem; }
  input, select { font: inherit; padding: 0.4rem 0.5rem; border: 1px solid #5c6370; border-radius: 4px; max-width: 100%; }
  input[aria-invalid='true'] { border-color: #b00020; border-width: 2px; }
  button, .btn-link {
    font: inherit; padding: 0.5rem 0.9rem; border: 2px solid #0b4fa8; border-radius: 4px;
    background: #0b4fa8; color: #fff; cursor: pointer; text-decoration: none; display: inline-block; margin: 0 0.5rem 0.5rem 0;
  }
  button.secondary, .btn-link.secondary { background: #fff; color: #0b4fa8; }
  button:disabled { background: #e1e4e8; border-color: #8a919c; color: #4a505a; cursor: not-allowed; }
  :is(a, button, input, select, [tabindex]):focus-visible { outline: 3px solid #1a73e8; outline-offset: 2px; }
  [tabindex='-1']:focus { outline: 3px solid #1a73e8; outline-offset: 2px; }
  .hint { color: #38404b; font-size: 0.95rem; margin: 0.25rem 0 0.75rem; }
  .field-error { color: #b00020; font-weight: 600; margin: 0.25rem 0 0.75rem; }
  .alert { border: 2px solid #b00020; background: #fdecee; color: #4a0010; padding: 0.75rem 1rem; border-radius: 4px; margin: 1rem 0; }
  .alert h2 { margin-top: 0; font-size: 1.1rem; }
  .warn { border: 2px solid #8a6d00; background: #fff8dc; color: #3d3000; padding: 0.75rem 1rem; border-radius: 4px; margin: 1rem 0; }
  .ok { border: 2px solid #1b6e2d; background: #eaf6ec; padding: 0.75rem 1rem; border-radius: 4px; margin: 1rem 0; }
  .status { min-height: 1.5rem; font-weight: 600; }
  dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.25rem 1rem; margin: 0.5rem 0 1rem; }
  dt { font-weight: 600; }
  dd { margin: 0; overflow-wrap: anywhere; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #c9ced6; padding: 0.4rem 0.5rem; text-align: left; vertical-align: top; }
  th { background: #f1f3f6; }
  .filters { display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end; margin-bottom: 0.75rem; }
  .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
`;
