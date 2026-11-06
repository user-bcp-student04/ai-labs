// src/app/qr-pagos/error-messages.spec.ts
import { guidanceFor, guidanceForDecode } from './error-messages';
import { QrDecodeError } from './qr-decoder.service';
import { ApiError } from './qr-pagos.models';

describe('error-messages (H03 CA-6)', () => {
  it('FE-ERR-01 cada código de negocio produce el título y la acción esperados', () => {
    const cases: Array<[number, string, string, string]> = [
      [400, 'QR_INVALID', 'El código QR no es válido', 'choose-another-qr'],
      [404, 'QR_UNKNOWN', 'QR no reconocido', 'choose-another-qr'],
      [410, 'QR_EXPIRED', 'El QR expiró', 'choose-another-qr'],
      [409, 'QR_CONFLICT', 'Los datos del comercio o del importe cambiaron', 'revalidate'],
      [422, 'AMOUNT_INVALID', 'Importe no válido', 'none'],
      [409, 'IDEMPOTENCY_CONFLICT', 'Solicitud repetida con datos distintos', 'none'],
      [413, 'PAYLOAD_TOO_LARGE', 'El contenido del QR es demasiado grande', 'choose-another-qr'],
      [200, 'RESPONSE_INVALID', 'Respuesta inesperada del servicio', 'none'],
    ];
    for (const [status, code, title, action] of cases) {
      const g = guidanceFor(new ApiError(status, code, null), 'resolve');
      expect(g.title).withContext(code).toBe(title);
      expect(g.action).withContext(code).toBe(action);
    }
  });

  it('FE-ERR-02 el conflicto de comercio/importe pide revalidar y no confirmar con datos previos', () => {
    const g = guidanceFor(new ApiError(409, 'QR_CONFLICT', null), 'payment');
    expect(g.action).toBe('revalidate');
    expect(g.detail).toContain('No confirmes con los datos anteriores');
  });

  it('FE-ERR-03 un 413 sin código se reconoce por el estado HTTP', () => {
    const g = guidanceFor(new ApiError(413, null, null), 'resolve');
    expect(g.title).toBe('El contenido del QR es demasiado grande');
    expect(g.action).toBe('choose-another-qr');
  });

  it('FE-ERR-04 401 y 403 producen un mensaje genérico de autorización', () => {
    for (const status of [401, 403]) {
      expect(guidanceFor(new ApiError(status, null, 'secreto'), 'payment').title).toBe('No tienes autorización');
    }
  });

  it('FE-ERR-05 el 404 solo es "pago/recibo no encontrado" en consultas de estado o recibo', () => {
    expect(guidanceFor(new ApiError(404, null, null), 'status').title).toBe('No se encontró el pago o el recibo');
    expect(guidanceFor(new ApiError(404, null, null), 'receipt').title).toBe('No se encontró el pago o el recibo');
    expect(guidanceFor(new ApiError(404, null, null), 'resolve').title).toBe('No se pudo completar la operación');
  });

  it('FE-ERR-06 sin conexión en un pago indica que se reutiliza la misma solicitud', () => {
    const pay = guidanceFor(new ApiError(0, null, null), 'payment');
    expect(pay.title).toBe('Sin conexión con el servicio');
    expect(pay.detail).toContain('se reutiliza la misma solicitud');
    const other = guidanceFor(new ApiError(0, null, null), 'resolve');
    expect(other.detail).not.toContain('se reutiliza la misma solicitud');
  });

  it('FE-ERR-07 un 5xx se muestra como fallo del servicio', () => {
    expect(guidanceFor(new ApiError(503, null, null), 'payment').title).toBe(
      'El servicio no pudo procesar la solicitud',
    );
  });

  it('FE-ERR-08 un código desconocido muestra el mensaje del servicio o el código', () => {
    expect(guidanceFor(new ApiError(418, 'X_RARO', 'texto del servicio'), 'resolve').detail).toBe('texto del servicio');
    expect(guidanceFor(new ApiError(418, 'X_RARO', null), 'resolve').detail).toContain('X_RARO');
    expect(guidanceFor(new ApiError(418, 'X_RARO', 'texto del servicio'), 'resolve').serviceMessage).toBe(
      'texto del servicio',
    );
  });

  it('FE-ERR-09 los errores de lectura local tienen su guía y no culpan al servicio', () => {
    expect(guidanceForDecode(new QrDecodeError('UNSUPPORTED')).title).toBe(
      'Tu navegador no puede leer QR desde imágenes',
    );
    expect(guidanceForDecode(new QrDecodeError('NOT_IMAGE')).title).toBe('El archivo no es una imagen');
    expect(guidanceForDecode(new QrDecodeError('NO_QR')).title).toBe('No se encontró un QR en la imagen');
    expect(guidanceForDecode(new QrDecodeError('READ_FAILED')).title).toBe('No se pudo leer la imagen');
    expect(guidanceForDecode(new QrDecodeError('NO_QR')).serviceMessage).toBeNull();
  });
});
