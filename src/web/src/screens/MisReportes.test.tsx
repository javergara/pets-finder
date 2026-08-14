import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Reporte } from '../api/types';
import { MisReportes } from './MisReportes';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    listarReportes: vi.fn(),
    marcarReunido: vi.fn(),
    editarReporte: vi.fn(),
  };
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
    raza: null,
    color: null,
    tamano: null,
    descripcion: 'Criollo color miel',
    foto_url: null,
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: null,
    lat: 4.54,
    lng: -75.68,
    situacion: null,
    fecha_evento: '2026-08-10',
    telefono_contacto: '3001234561',
    instagram: null,
    facebook: null,
    fuente: 'manual',
    crawl_metadata: null,
    idempotency_id: null,
    estado: 'activo',
    creado_en: '2026-08-12T08:00:00',
    resuelto_en: null,
    ...overrides,
  };
}

function renderMisReportes() {
  return render(
    <MemoryRouter>
      <MisReportes />
    </MemoryRouter>,
  );
}

describe('MisReportes', () => {
  it('lista mis reportes (incluidos los reunidos) pidiendo estado=todos', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue([
      crearReporte(),
      crearReporte({ id: 2, nombre_mascota: 'Firulais', estado: 'reunido' }),
    ]);

    renderMisReportes();

    expect(await screen.findByText('Rocky')).toBeInTheDocument();
    expect(screen.getByText('Firulais')).toBeInTheDocument();
    expect(screen.getByText('Reunida 💚')).toBeInTheDocument();
    expect(client.listarReportes).toHaveBeenCalledWith({ userId: 1, estado: 'todos' });
  });

  it('marcar como reunida llama al backend y recarga la lista', async () => {
    vi.mocked(client.listarReportes)
      .mockResolvedValueOnce([crearReporte()])
      .mockResolvedValueOnce([crearReporte({ estado: 'reunido' })]);
    vi.mocked(client.marcarReunido).mockResolvedValue(crearReporte({ estado: 'reunido' }));

    renderMisReportes();
    fireEvent.click(await screen.findByRole('button', { name: 'Marcar como reunida' }));

    await screen.findByText('Reunida 💚');
    expect(client.marcarReunido).toHaveBeenCalledWith(1, 1);
    expect(client.listarReportes).toHaveBeenCalledTimes(2);
  });

  it('editar guarda descripción y teléfono nuevos vía PUT', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue([crearReporte()]);
    vi.mocked(client.editarReporte).mockResolvedValue(
      crearReporte({ descripcion: 'Visto cerca del parque' }),
    );

    renderMisReportes();
    fireEvent.click(await screen.findByRole('button', { name: 'Editar' }));
    fireEvent.change(screen.getByLabelText('Descripción y señas'), {
      target: { value: 'Visto cerca del parque' },
    });
    fireEvent.change(screen.getByLabelText('Teléfono de contacto'), {
      target: { value: '3009998877' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }));

    await waitFor(() =>
      expect(client.editarReporte).toHaveBeenCalledWith(1, {
        user_id: 1,
        descripcion: 'Visto cerca del parque',
        telefono_contacto: '3009998877',
      }),
    );
  });

  it('un reporte reunido no ofrece acciones', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue([crearReporte({ estado: 'reunido' })]);

    renderMisReportes();

    await screen.findByText('Reunida 💚');
    expect(screen.queryByRole('button', { name: 'Marcar como reunida' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Editar' })).not.toBeInTheDocument();
  });
});
