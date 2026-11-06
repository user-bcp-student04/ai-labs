// src/app/qr-pagos/error-messages.ts
import { QrDecodeError } from './qr-decoder.service';
import { ApiError } from './qr-pagos.models';

export type GuidanceAction = 'choose-another-qr' | 'revalidate' | 'none';
export type GuidanceContext = 'resolve' | 'payment' | 'status' | 'receipt';

export interface Guidance {
  title: string;
  detail: string;
  action: GuidanceAction;
  /** Mensaje textual devuelto por el servicio, si existe. */
  serviceMessage: string | null;
}

export function guidanceForDecode(error: QrDecodeError): Guidance {
  switch (error.reason) {
    case 'UNSUPPORTED':
      return {
        title: 'Tu navegador no puede leer QR desde imágenes',
        detail:
          'Prueba con un navegador compatible con BarcodeDetector (por ejemplo, Chrome en Android, macOS o ChromeOS). No se envió nada al servicio.',
        action: 'none',
        serviceMessage: null,
      };
    case 'NOT_IMAGE':
      return {
        title: 'El archivo no es una imagen',
        detail: 'Elige una imagen (PNG, JPG, etc.) que contenga el código QR del comercio.',
        action: 'choose-another-qr',
        serviceMessage: null,
      };
    case 'NO_QR':
      return {
        title: 'No se encontró un QR en la imagen',
        detail: 'Verifica que la imagen sea nítida y muestre el QR completo, o carga otra imagen.',
        action: 'choose-another-qr',
        serviceMessage: null,
      };
    default:
      return {
        title: 'No se pudo leer la imagen',
        detail: 'El archivo no se pudo procesar. Carga otra imagen.',
        action: 'choose-another-qr',
        serviceMessage: null,
      };
  }
}

export function guidanceFor(error: ApiError, context: GuidanceContext): Guidance {
  const serviceMessage = error.serviceMessage;
  const make = (title: string, detail: string, action: GuidanceAction = 'none'): Guidance => ({
    title,
    detail,
    action,
    serviceMessage,
  });

  switch (error.code) {
    case 'QR_INVALID':
      return make(
        'El código QR no es válido',
        'No se pudo validar el contenido de la imagen. Verifica que sea el QR completo del comercio o carga otra imagen.',
        'choose-another-qr',
      );
    case 'QR_UNKNOWN':
      return make(
        'QR no reconocido',
        'Este QR no corresponde a un comercio conocido. Confirma con el comercio que sea su QR de pago.',
        'choose-another-qr',
      );
    case 'QR_EXPIRED':
      return make(
        'El QR expiró',
        'Pide al comercio un QR vigente y cárgalo. La respuesta indica que el pago no se realizó.',
        'choose-another-qr',
      );
    case 'QR_CONFLICT':
      return make(
        'Los datos del comercio o del importe cambiaron',
        'Hay un conflicto entre el QR y el pago. No confirmes con los datos anteriores: vuelve a validar el QR para ver los datos actuales.',
        'revalidate',
      );
    case 'AMOUNT_INVALID':
      return make('Importe no válido', 'Ingresa un importe mayor que 0 y vuelve a confirmar.');
    case 'IDEMPOTENCY_CONFLICT':
      return make(
        'Solicitud repetida con datos distintos',
        'Se generará una solicitud nueva. Revisa los datos y confirma de nuevo.',
      );
    case 'PAYLOAD_TOO_LARGE':
      return make(
        'El contenido del QR es demasiado grande',
        'El servicio rechazó el contenido. Elige otro QR.',
        'choose-another-qr',
      );
    case 'RESPONSE_INVALID':
      return make(
        'Respuesta inesperada del servicio',
        'El servicio devolvió datos que no cumplen el contrato esperado. No se muestra ningún pago como creado; revisa el historial o inténtalo más tarde.',
      );
    default:
      break;
  }

  if (error.status === 413) {
    return make(
      'El contenido del QR es demasiado grande',
      'El servicio rechazó el contenido. Elige otro QR.',
      'choose-another-qr',
    );
  }
  if (error.status === 401 || error.status === 403) {
    return make('No tienes autorización', 'El servicio rechazó la solicitud por falta de autorización.');
  }
  if (error.status === 404 && (context === 'status' || context === 'receipt')) {
    return make(
      'No se encontró el pago o el recibo',
      'El servicio no tiene información para este pago todavía. Inténtalo más tarde.',
    );
  }
  if (error.status === 0) {
    return make(
      'Sin conexión con el servicio',
      context === 'payment'
        ? 'No se pudo contactar al servicio. Verifica tu conexión y vuelve a pulsar «Confirmar pago»: se reutiliza la misma solicitud, así se evita un cobro duplicado.'
        : 'No se pudo contactar al servicio. Verifica tu conexión o que el servicio esté disponible e inténtalo de nuevo.',
    );
  }
  if (error.status >= 500) {
    return make(
      'El servicio no pudo procesar la solicitud',
      context === 'payment'
        ? 'Inténtalo de nuevo. Si repites «Confirmar pago», se reutiliza la misma solicitud.'
        : 'Inténtalo de nuevo en unos minutos.',
    );
  }
  return make(
    'No se pudo completar la operación',
    serviceMessage ?? `El servicio respondió con el código ${error.code ?? error.status}.`,
  );
}
