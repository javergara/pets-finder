import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import * as imagen from '../lib/imagen';
import { FotoUpload } from './FotoUpload';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, subirFoto: vi.fn() };
});

vi.mock('../lib/imagen', () => ({ comprimirImagen: vi.fn(), recortarImagen: vi.fn() }));

// Cropper real necesita cargar la imagen y medir el contenedor (imposible en
// jsdom): el stub expone un botón que simula que el usuario ajustó el encuadre.
vi.mock('react-easy-crop', async () => {
  const { createElement } = await import('react');
  return {
    default: ({
      onCropComplete,
    }: {
      onCropComplete?: (area: unknown, areaPixeles: unknown) => void;
    }) =>
      createElement(
        'button',
        {
          type: 'button',
          onClick: () => onCropComplete?.(null, { x: 10, y: 20, width: 300, height: 200 }),
        },
        'simular-encuadre',
      ),
  };
});

beforeEach(() => {
  // Pass-through por defecto: recorte y compresión reales se testean en lib/imagen.test.ts.
  vi.mocked(imagen.comprimirImagen).mockImplementation(async (archivo) => archivo);
  vi.mocked(imagen.recortarImagen).mockImplementation(async (archivo) => archivo);
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
  it('muestra el paso de recorte al elegir archivo y sube el original si no se ajusta nada', async () => {
    vi.mocked(client.subirFoto).mockResolvedValue({ foto_url: '/media/uploads/abc123.jpg' });
    const onFotoSubida = vi.fn();

    render(<FotoUpload onFotoSubida={onFotoSubida} />);
    const archivo = elegirArchivo();

    // Aparece el encuadre, todavía no se sube nada.
    expect(screen.getByText('simular-encuadre')).toBeInTheDocument();
    expect(client.subirFoto).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Subir foto' }));

    await waitFor(() => expect(onFotoSubida).toHaveBeenCalledWith('/media/uploads/abc123.jpg'));
    // Sin encuadre ajustado no se pasa por recortarImagen: va el archivo elegido.
    expect(imagen.recortarImagen).not.toHaveBeenCalled();
    expect(client.subirFoto).toHaveBeenCalledWith(archivo);
    expect(screen.getByText('Foto lista.')).toBeInTheDocument();
    // El paso de recorte se cierra y queda el preview final.
    expect(screen.getByAltText('Vista previa de la foto elegida')).toHaveAttribute(
      'src',
      'blob:preview-local',
    );
  });

  it('con el encuadre ajustado sube la versión recortada', async () => {
    const recortada = new File(['recorte'], 'rocky.jpg', { type: 'image/jpeg' });
    vi.mocked(imagen.recortarImagen).mockResolvedValue(recortada);
    vi.mocked(client.subirFoto).mockResolvedValue({ foto_url: '/media/uploads/abc123.jpg' });

    render(<FotoUpload onFotoSubida={vi.fn()} />);
    const original = elegirArchivo();

    fireEvent.click(screen.getByText('simular-encuadre'));
    fireEvent.click(screen.getByRole('button', { name: 'Subir foto' }));

    await waitFor(() =>
      expect(imagen.recortarImagen).toHaveBeenCalledWith(original, {
        x: 10,
        y: 20,
        width: 300,
        height: 200,
      }),
    );
    await waitFor(() => expect(client.subirFoto).toHaveBeenCalledWith(recortada));
  });

  it('sube la versión comprimida que devuelve comprimirImagen, no el original', async () => {
    const comprimida = new File(['mini'], 'rocky.jpg', { type: 'image/jpeg' });
    vi.mocked(imagen.comprimirImagen).mockResolvedValue(comprimida);
    vi.mocked(client.subirFoto).mockResolvedValue({ foto_url: '/media/uploads/abc123.jpg' });

    render(<FotoUpload onFotoSubida={vi.fn()} />);
    const original = elegirArchivo();
    fireEvent.click(screen.getByRole('button', { name: 'Subir foto' }));

    await waitFor(() => expect(client.subirFoto).toHaveBeenCalledWith(comprimida));
    expect(imagen.comprimirImagen).toHaveBeenCalledWith(original);
  });

  it('cancelar cierra el paso de recorte sin subir nada', () => {
    render(<FotoUpload onFotoSubida={vi.fn()} />);
    elegirArchivo();

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));

    expect(screen.queryByText('simular-encuadre')).not.toBeInTheDocument();
    expect(client.subirFoto).not.toHaveBeenCalled();
  });

  it('muestra el mensaje del backend si la subida falla y no entrega foto_url', async () => {
    vi.mocked(client.subirFoto).mockRejectedValue(
      new client.ApiError('La foto supera el tamaño máximo de 5 MB.'),
    );
    const onFotoSubida = vi.fn();

    render(<FotoUpload onFotoSubida={onFotoSubida} />);
    elegirArchivo();
    fireEvent.click(screen.getByRole('button', { name: 'Subir foto' }));

    await screen.findByText('La foto supera el tamaño máximo de 5 MB.');
    expect(onFotoSubida).not.toHaveBeenCalled();
  });
});
