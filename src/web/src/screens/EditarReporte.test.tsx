import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Reporte } from '../api/types';
import { ZONAS } from '../lib/ciudades';
import { EditarReporte } from './EditarReporte';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerReporte: vi.fn(), editarReporte: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
});

function crearReporte(overrides: Partial<Reporte> = {}): Reporte {
  return {
    id: 1,
    user_id: 1,
    tipo: 'perdido',
    especie: 'perro',
    nombre_mascota: 'Rocky',
    raza: 'Labrador',
    color: 'Negro',
    tamano: 'grande',
    descripcion: 'Criollo color miel con collar rojo',
    foto_url: '/media/seed/report_1.jpg',
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: 'La Castellana',
    lat: ZONAS.Armenia.centroLat,
    lng: ZONAS.Armenia.centroLng,
    situacion: null,
    fecha_evento: '2026-08-10',
    telefono_contacto: '3001234561',
    instagram: null,
    facebook: null,
    estado: 'activo',
    creado_en: '2026-08-12T08:00:00',
    resuelto_en: null,
    necesidades_pendientes: 0,
    ...overrides,
  } as Reporte;
}

function renderEditar() {
  return render(
    <MemoryRouter initialEntries={['/reporte/1/editar']}>
      <Routes>
        <Route path="/reporte/:id/editar" element={<EditarReporte />} />
        <Route path="/reporte/:id" element={<div>Detalle stub</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('EditarReporte', () => {
  it('llega precargado con los valores actuales del reporte', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());

    renderEditar();

    expect(await screen.findByLabelText('Descripción y señas')).toHaveValue(
      'Criollo color miel con collar rojo',
    );
    expect(screen.getByLabelText('Raza')).toHaveValue('Labrador');
    expect(screen.getByLabelText('Color')).toHaveValue('Negro');
    expect(screen.getByLabelText('Tamaño')).toHaveValue('grande');
    expect(screen.getByLabelText('Barrio (opcional)')).toHaveValue('La Castellana');
    expect(screen.getByLabelText('¿Cuándo se perdió?')).toHaveValue('2026-08-10');
    expect(screen.getByLabelText('Teléfono de contacto (WhatsApp)')).toHaveValue('3001234561');
    // La zona se muestra pero no es editable.
    expect(screen.getByText(/Zona: Armenia \(no se puede cambiar/)).toBeInTheDocument();
  });

  it('guardar envía los cambios y navega al detalle', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());
    vi.mocked(client.editarReporte).mockResolvedValue(crearReporte({ color: 'Blanco' }));

    renderEditar();

    fireEvent.change(await screen.findByLabelText('Color'), { target: { value: 'Blanco' } });
    fireEvent.change(screen.getByLabelText('¿Cuándo se perdió?'), {
      target: { value: '2026-08-09' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }));

    await screen.findByText('Detalle stub');
    expect(client.editarReporte).toHaveBeenCalledWith(
      1,
      expect.objectContaining({
        user_id: 1,
        color: 'Blanco',
        fecha_evento: '2026-08-09',
        raza: 'Labrador',
        tamano: 'grande',
        // Sin click en el mapa (jsdom), el pin conserva las coords actuales.
        lat: ZONAS.Armenia.centroLat,
        lng: ZONAS.Armenia.centroLng,
      }),
    );
  });

  it('quien no es el autor es devuelto al detalle sin ver el formulario', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte({ user_id: 2 }));

    renderEditar();

    await screen.findByText('Detalle stub');
    expect(screen.queryByLabelText('Descripción y señas')).not.toBeInTheDocument();
  });

  it('valida los obligatorios antes de llamar al API', async () => {
    vi.mocked(client.obtenerReporte).mockResolvedValue(crearReporte());

    renderEditar();

    fireEvent.change(await screen.findByLabelText('Descripción y señas'), {
      target: { value: '   ' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }));

    expect(
      await screen.findByText('La descripción y el teléfono de contacto son obligatorios.'),
    ).toBeInTheDocument();
    await waitFor(() => expect(client.editarReporte).not.toHaveBeenCalled());
  });
});
