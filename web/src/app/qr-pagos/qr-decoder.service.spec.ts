// src/app/qr-pagos/qr-decoder.service.spec.ts
import { TestBed } from '@angular/core/testing';

import { QR_IMAGE_ENGINE, QrDecodeError, QrDecoderService, QrImageEngine } from './qr-decoder.service';

async function pngFile(): Promise<File> {
  const canvas = document.createElement('canvas');
  canvas.width = 8;
  canvas.height = 8;
  const blob = await new Promise<Blob>((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('toBlob falló'))), 'image/png'),
  );
  return new File([blob], 'qr.png', { type: 'image/png' });
}

describe('QrDecoderService (H03 CA-1)', () => {
  let decodeSpy: jasmine.Spy;

  function setup(available: boolean, impl: () => Promise<string | null>): QrDecoderService {
    decodeSpy = jasmine.createSpy('decode').and.callFake(impl);
    const engine: QrImageEngine = { available, decode: decodeSpy as unknown as QrImageEngine['decode'] };
    TestBed.configureTestingModule({
      providers: [QrDecoderService, { provide: QR_IMAGE_ENGINE, useValue: engine }],
    });
    return TestBed.inject(QrDecoderService);
  }

  it('FE-DEC-01 devuelve solo el texto del QR y entrega un ImageBitmap al motor', async () => {
    const svc = setup(true, async () => 'PAYLOAD-QR');
    const text = await svc.decode(await pngFile());
    expect(text).toBe('PAYLOAD-QR');
    expect(decodeSpy.calls.argsFor(0)[0] instanceof ImageBitmap).toBeTrue();
  });

  it('FE-DEC-02 rechaza un archivo que no es imagen sin invocar al motor', async () => {
    const svc = setup(true, async () => 'X');
    const file = new File(['hola'], 'nota.txt', { type: 'text/plain' });
    await expectAsync(svc.decode(file)).toBeRejectedWith(jasmine.objectContaining({ reason: 'NOT_IMAGE' }));
    expect(decodeSpy).not.toHaveBeenCalled();
  });

  it('FE-DEC-03 informa UNSUPPORTED si el motor no está disponible', async () => {
    const svc = setup(false, async () => 'X');
    await expectAsync(svc.decode(await pngFile())).toBeRejectedWith(
      jasmine.objectContaining({ reason: 'UNSUPPORTED' }),
    );
    expect(decodeSpy).not.toHaveBeenCalled();
  });

  it('FE-DEC-04 informa NO_QR si el motor no encuentra texto', async () => {
    const svc = setup(true, async () => null);
    await expectAsync(svc.decode(await pngFile())).toBeRejectedWith(jasmine.objectContaining({ reason: 'NO_QR' }));
  });

  it('FE-DEC-05 trata el texto vacío como NO_QR (borde)', async () => {
    const svc = setup(true, async () => '');
    await expectAsync(svc.decode(await pngFile())).toBeRejectedWith(jasmine.objectContaining({ reason: 'NO_QR' }));
  });

  it('FE-DEC-06 informa READ_FAILED si el motor lanza o la imagen es ilegible', async () => {
    const failing = setup(true, async () => {
      throw new Error('motor roto');
    });
    await expectAsync(failing.decode(await pngFile())).toBeRejectedWith(
      jasmine.objectContaining({ reason: 'READ_FAILED' }),
    );

    const corrupt = new File(['no-es-un-png'], 'roto.png', { type: 'image/png' });
    await expectAsync(failing.decode(corrupt)).toBeRejectedWith(jasmine.objectContaining({ reason: 'READ_FAILED' }));
    expect(new QrDecodeError('NO_QR').reason).toBe('NO_QR');
  });
});
