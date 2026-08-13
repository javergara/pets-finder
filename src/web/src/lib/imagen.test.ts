import { afterEach, describe, expect, it, vi } from 'vitest';
import { CALIDAD_JPEG, comprimirImagen, LADO_MAXIMO, recortarImagen } from './imagen';

function crearArchivo(bytes: number, nombre = 'foto.png'): File {
  return new File([new Uint8Array(bytes)], nombre, { type: 'image/png' });
}

// jsdom no implementa canvas: se interpone solo en createElement('canvas'),
// dejando pasar el resto de elementos (React sigue renderizando normal).
function stubCanvas(blobResultante: Blob | null) {
  const drawImage = vi.fn();
  const toBlob = vi.fn((cb: BlobCallback) => cb(blobResultante));
  const canvas = {
    width: 0,
    height: 0,
    getContext: vi.fn(() => ({ drawImage })),
    toBlob,
  };
  const original = document.createElement.bind(document);
  vi.spyOn(document, 'createElement').mockImplementation((tag: string) =>
    tag === 'canvas' ? (canvas as unknown as HTMLElement) : original(tag),
  );
  return { canvas, drawImage, toBlob };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('comprimirImagen', () => {
  it('sin soporte del navegador (jsdom sin createImageBitmap) devuelve el original', async () => {
    const archivo = crearArchivo(5000);

    expect(await comprimirImagen(archivo)).toBe(archivo);
  });

  it('reescala al lado máximo y devuelve un JPEG más pequeño', async () => {
    const archivo = crearArchivo(4_000_000);
    const close = vi.fn();
    vi.stubGlobal(
      'createImageBitmap',
      vi.fn(async () => ({ width: 4000, height: 3000, close })),
    );
    const { canvas, drawImage, toBlob } = stubCanvas(
      new Blob([new Uint8Array(200_000)], { type: 'image/jpeg' }),
    );

    const resultado = await comprimirImagen(archivo);

    // 4000x3000 reescalado por el lado mayor → 1280x960.
    expect(canvas.width).toBe(LADO_MAXIMO);
    expect(canvas.height).toBe(960);
    expect(drawImage).toHaveBeenCalledWith(expect.anything(), 0, 0, LADO_MAXIMO, 960);
    expect(toBlob).toHaveBeenCalledWith(expect.any(Function), 'image/jpeg', CALIDAD_JPEG);
    expect(close).toHaveBeenCalled();
    expect(resultado.type).toBe('image/jpeg');
    expect(resultado.name).toBe('foto.jpg');
    expect(resultado.size).toBe(200_000);
  });

  it('si el JPEG no queda más pequeño que el original, devuelve el original', async () => {
    const archivo = crearArchivo(1000);
    vi.stubGlobal(
      'createImageBitmap',
      vi.fn(async () => ({ width: 100, height: 100, close: vi.fn() })),
    );
    stubCanvas(new Blob([new Uint8Array(5000)], { type: 'image/jpeg' }));

    expect(await comprimirImagen(archivo)).toBe(archivo);
  });
});

describe('recortarImagen', () => {
  it('sin soporte del navegador (jsdom sin createImageBitmap) devuelve el original', async () => {
    const archivo = crearArchivo(5000);

    expect(await recortarImagen(archivo, { x: 0, y: 0, width: 10, height: 10 })).toBe(archivo);
  });

  it('recorta el área pedida sobre un canvas y devuelve un JPEG con ese tamaño', async () => {
    const archivo = crearArchivo(100_000);
    const close = vi.fn();
    vi.stubGlobal(
      'createImageBitmap',
      vi.fn(async () => ({ width: 1000, height: 800, close })),
    );
    const { canvas, drawImage, toBlob } = stubCanvas(
      new Blob([new Uint8Array(40_000)], { type: 'image/jpeg' }),
    );

    const resultado = await recortarImagen(archivo, { x: 100, y: 50, width: 400, height: 300 });

    expect(canvas.width).toBe(400);
    expect(canvas.height).toBe(300);
    expect(drawImage).toHaveBeenCalledWith(expect.anything(), 100, 50, 400, 300, 0, 0, 400, 300);
    expect(toBlob).toHaveBeenCalledWith(expect.any(Function), 'image/jpeg', 0.92);
    expect(close).toHaveBeenCalled();
    expect(resultado.type).toBe('image/jpeg');
    expect(resultado.name).toBe('foto.jpg');
    expect(resultado.size).toBe(40_000);
  });

  it('si el área cubre la imagen completa devuelve el original sin re-codificar', async () => {
    const archivo = crearArchivo(100_000);
    vi.stubGlobal(
      'createImageBitmap',
      vi.fn(async () => ({ width: 1000, height: 800, close: vi.fn() })),
    );
    const { toBlob } = stubCanvas(new Blob([new Uint8Array(1)], { type: 'image/jpeg' }));

    expect(await recortarImagen(archivo, { x: 0, y: 0, width: 1000, height: 800 })).toBe(archivo);
    expect(toBlob).not.toHaveBeenCalled();
  });
});
