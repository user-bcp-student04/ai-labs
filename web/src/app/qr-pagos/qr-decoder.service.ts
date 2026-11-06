// src/app/qr-pagos/qr-decoder.service.ts
import { Injectable, InjectionToken, inject } from '@angular/core';

/**
 * Motor de lectura de QR sobre un bitmap. El motor por defecto usa la API nativa
 * BarcodeDetector (sin dependencias nuevas). Si el proyecto aprueba una librería
 * (P-3), se provee otro motor con este token sin cambiar los componentes.
 */
export interface QrImageEngine {
  readonly available: boolean;
  decode(image: ImageBitmap): Promise<string | null>;
}

interface BarcodeDetectorLike {
  detect(image: ImageBitmap): Promise<Array<{ rawValue?: string }>>;
}
type BarcodeDetectorCtor = new (options: { formats: string[] }) => BarcodeDetectorLike;

function createNativeEngine(): QrImageEngine {
  const ctor = (globalThis as unknown as { BarcodeDetector?: BarcodeDetectorCtor }).BarcodeDetector;
  return {
    available: typeof ctor === 'function',
    async decode(image: ImageBitmap): Promise<string | null> {
      if (!ctor) {
        return null;
      }
      const codes = await new ctor({ formats: ['qr_code'] }).detect(image);
      const found = codes.find((c) => typeof c.rawValue === 'string' && c.rawValue.length > 0);
      return found?.rawValue ?? null;
    },
  };
}

export const QR_IMAGE_ENGINE = new InjectionToken<QrImageEngine>('QR_IMAGE_ENGINE', {
  providedIn: 'root',
  factory: createNativeEngine,
});

export type QrDecodeReason = 'UNSUPPORTED' | 'NOT_IMAGE' | 'NO_QR' | 'READ_FAILED';

export class QrDecodeError extends Error {
  constructor(readonly reason: QrDecodeReason) {
    super(reason);
  }
}

@Injectable()
export class QrDecoderService {
  private readonly engine = inject(QR_IMAGE_ENGINE);

  /** Decodifica la imagen en el navegador y devuelve solo el texto del QR. */
  async decode(file: File): Promise<string> {
    if (!file.type.startsWith('image/')) {
      throw new QrDecodeError('NOT_IMAGE');
    }
    if (!this.engine.available) {
      throw new QrDecodeError('UNSUPPORTED');
    }

    let bitmap: ImageBitmap;
    try {
      bitmap = await createImageBitmap(file);
    } catch {
      throw new QrDecodeError('READ_FAILED');
    }

    try {
      const text = await this.engine.decode(bitmap);
      if (!text) {
        throw new QrDecodeError('NO_QR');
      }
      return text;
    } catch (error) {
      if (error instanceof QrDecodeError) {
        throw error;
      }
      throw new QrDecodeError('READ_FAILED');
    } finally {
      bitmap.close();
    }
  }
}
