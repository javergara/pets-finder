import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import * as imagen from '../lib/imagen';
import { FotoUpload } from './FotoUpload';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, subirFoto: vi.fn() };
});

vi.mock('../lib/imagen', () => ({ comprimirImagen: vi.fn() }));

beforeEach(() => {
  // Pass-through por defecto: la compresión real se testea en lib/imagen.test.ts.
  vi.mocked(imagen.comprimirImagen).mockImplementation(async (archivo) => archivo);
  // jsdom no implementa object URLs.
  vi.stubGlobal('URL', {
    ...URL,
    createObjectURL: vi.fn(() => 'blob:preview-local'),
    revokeObjectURL: vi.fn(),
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.resetAllMocks();
});

function elegirArchivo() {
  const archivo = new File(['bytes'], 'rocky.jpg', { type: 'image/jpeg' });
  fireEvent.change(screen.getByLabelText('Foto de la mascota'), {
    target: { files: [archivo] },
  });
  return archivo;
}

describe('FotoUpload', () => {
  it('muestra el preview local al elegir archivo y entrega el foto_url al terminar', async () => {
    vi.mocked(client.subirFoto).mockResolvedValue({ foto_url: '/media/uploads/abc123.jpg' });
    const onFotoSubida = vi.fn();

    render(<FotoUpload onFotoSubida={onFotoSubida} />);
    const archivo = elegirArchivo();

    expect(screen.getByAltText('Vista previa de la foto elegida')).toHaveAttribute(
      'src',
      'blob:preview-local',
    );
    await waitFor(() => expect(onFotoSubida).toHaveBeenCalledWith('/media/uploads/abc123.jpg'));
    expect(client.subirFoto).toHaveBeenCalledWith(archivo);
    expect(screen.getByText('Foto lista.')).toBeInTheDocument();
  });

  it('sube la versión comprimida que devuelve comprimirImagen, no el original', async () => {
    const comprimida = new File(['mini'], 'rocky.jpg', { type: 'image/jpeg' });
    vi.mocked(imagen.comprimirImagen).mockResolvedValue(comprimida);
    vi.mocked(client.subirFoto).mockResolvedValue({ foto_url: '/media/uploads/abc123.jpg' });

    render(<FotoUpload onFotoSubida={vi.fn()} />);
    const original = elegirArchivo();

    await waitFor(() => expect(client.subirFoto).toHaveBeenCalledWith(comprimida));
    expect(imagen.comprimirImagen).toHaveBeenCalledWith(original);
  });

  it('muestra el mensaje del backend si la subida falla y no entrega foto_url', async () => {
    vi.mocked(client.subirFoto).mockRejectedValue(
      new client.ApiError('La foto supera el tamaño máximo de 5 MB.'),
    );
    const onFotoSubida = vi.fn();

    render(<FotoUpload onFotoSubida={onFotoSubida} />);
    elegirArchivo();

    await screen.findByText('La foto supera el tamaño máximo de 5 MB.');
    expect(onFotoSubida).not.toHaveBeenCalled();
  });
});
