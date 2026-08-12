import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Reporte } from '../api/types';
import { MapaReportes } from './MapaReportes';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, listarReportes: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function crearReporte(overrides: Partial<Reporte> = {}): Reporte {
  return {
    id: 1,
    user_id: 1,
    tipo: 'perdido',
    especie: 'perro',
    nombre_mascota: 'Rocky',
    descripcion: 'd',
    foto_url: null,
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: null,
    lat: 4.54,
    lng: -75.68,
    situacion: null,
    fecha_evento: '2026-08-10',
    telefono_contacto: '300',
    estado: 'activo',
    creado_en: '2026-08-12T08:00:00',
    resuelto_en: null,
    ...overrides,
  };
}

const REPORTES = [
  crearReporte(),
  crearReporte({
    id: 2,
    tipo: 'encontrado',
    especie: 'gato',
    nombre_mascota: null,
    situacion: 'conmigo',
    zona: 'Cali',
    lat: 3.45,
    lng: -76.53,
  }),
  crearReporte({ id: 3, nombre_mascota: 'Canela', zona: 'Quibdó', lat: 5.695, lng: -76.66 }),
];

function renderMapa() {
  return render(
    <MemoryRouter>
      <MapaReportes />
    </MemoryRouter>,
  );
}

describe('MapaReportes', () => {
  it('la vista Todo Colombia plotea reportes de todas las zonas a la vez', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue(REPORTES);

    renderMapa();

    expect(await screen.findByRole('button', { name: 'Reporte: Rocky' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reporte: Gato' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reporte: Canela' })).toBeInTheDocument();
    expect(screen.getByText('3 reportes activos en todo Colombia.')).toBeInTheDocument();
  });

  it('los pins usan bg-danger para perdidos y bg-forest para encontrados, con leyenda', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue(REPORTES);

    renderMapa();

    const pinPerdido = await screen.findByRole('button', { name: 'Reporte: Rocky' });
    const pinEncontrado = screen.getByRole('button', { name: 'Reporte: Gato' });
    expect(pinPerdido.className).toContain('bg-danger');
    expect(pinEncontrado.className).toContain('bg-forest');

    expect(screen.getByText('Mascota perdida')).toBeInTheDocument();
    expect(screen.getByText('Mascota encontrada')).toBeInTheDocument();
  });

  it('elegir una zona muestra solo sus reportes', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue(REPORTES);

    renderMapa();
    await screen.findByRole('button', { name: 'Reporte: Rocky' });

    fireEvent.change(screen.getByLabelText('Zona'), { target: { value: 'Cali' } });

    expect(screen.getByRole('button', { name: 'Reporte: Gato' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Reporte: Rocky' })).not.toBeInTheDocument();
    expect(screen.getByText('1 reportes activos en Cali.')).toBeInTheDocument();
  });

  it('click en un pin abre la mini-tarjeta con el link al detalle', async () => {
    vi.mocked(client.listarReportes).mockResolvedValue(REPORTES);

    renderMapa();

    fireEvent.click(await screen.findByRole('button', { name: 'Reporte: Canela' }));

    expect(screen.getByText('Canela')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ver reporte' })).toHaveAttribute('href', '/reporte/3');
  });
});
