import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Organizacion, Reporte } from '../api/types';
import { ZonaLanding } from './ZonaLanding';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    obtenerConteos: vi.fn(),
    listarReportesPaginado: vi.fn(),
    listarOrganizaciones: vi.fn(),
  };
});

beforeEach(() => {
  vi.mocked(client.obtenerConteos).mockResolvedValue({ perdidos: 5, encontrados: 3 });
  vi.mocked(client.listarReportesPaginado).mockResolvedValue({ items: [], total: 0 });
  vi.mocked(client.listarOrganizaciones).mockResolvedValue([]);
});

afterEach(() => {
  vi.resetAllMocks();
});

function reporte(overrides: Partial<Reporte> = {}): Reporte {
  return {
    id: 1,
    user_id: 1,
    tipo: 'perdido',
    especie: 'perro',
    nombre_mascota: 'Rocky',
    raza: null,
    color: null,
    tamano: null,
    descripcion: 'x',
    foto_url: null,
    zona: 'Cali',
    ciudad_texto: null,
    barrio: null,
    lat: 3.45,
    lng: -76.53,
    situacion: null,
    fecha_evento: '2026-08-10',
    telefono_contacto: '300',
    instagram: null,
    facebook: null,
    fuente: 'manual',
    crawl_metadata: null,
    idempotency_id: null,
    estado: 'activo',
    creado_en: new Date().toISOString(),
    resuelto_en: null,
    ...overrides,
  };
}

function organizacion(overrides: Partial<Organizacion> = {}): Organizacion {
  return {
    id: 1,
    user_id: 70,
    tipo: 'veterinaria',
    nombre: 'Servivet',
    descripcion: 'x',
    zona: 'Cali',
    ciudad_texto: null,
    barrio: null,
    direccion: 'Cl. 16 #56-55',
    lat: 3.4,
    lng: -76.5,
    telefono_contacto: '300',
    horario: 'Urgencias 24 horas',
    como_donar: null,
    foto_url: null,
    estado: 'activo',
    creado_en: new Date().toISOString(),
    necesidades_pendientes: 0,
    ...overrides,
  };
}

function renderZona() {
  return render(
    <MemoryRouter initialEntries={['/cali']}>
      <ZonaLanding zona="Cali" />
    </MemoryRouter>,
  );
}

describe('ZonaLanding', () => {
  it('muestra el título de la zona, los conteos y fija el document.title', async () => {
    renderZona();

    expect(
      screen.getByRole('heading', { name: 'Mascotas perdidas y encontradas en Cali' }),
    ).toBeInTheDocument();
    expect(await screen.findByText('5 perdidas')).toBeInTheDocument();
    expect(screen.getByText('3 encontradas')).toBeInTheDocument();
    expect(document.title).toBe('Mascotas perdidas y encontradas en Cali | Pet Finder Col');
    // Los datos se piden con la zona.
    expect(client.obtenerConteos).toHaveBeenCalledWith('Cali');
    expect(client.listarReportesPaginado).toHaveBeenCalledWith({ zona: 'Cali' }, 6, 0);
  });

  it('lista los reportes recientes y las organizaciones de la zona', async () => {
    vi.mocked(client.listarReportesPaginado).mockResolvedValue({
      items: [reporte()],
      total: 1,
    });
    vi.mocked(client.listarOrganizaciones).mockResolvedValue([
      organizacion(),
      organizacion({ id: 2, tipo: 'fundacion', nombre: 'Fundación Patitas Rosas', horario: null }),
    ]);

    renderZona();

    expect(await screen.findByText('Rocky')).toBeInTheDocument();
    expect(screen.getByText('Servivet')).toBeInTheDocument();
    expect(screen.getByText('24 horas')).toBeInTheDocument();
    expect(screen.getByText('Fundación Patitas Rosas')).toBeInTheDocument();
  });

  it('los CTAs llevan a reportar, buscar y mapa', () => {
    renderZona();

    expect(screen.getByRole('link', { name: 'Perdí a mi mascota' })).toHaveAttribute(
      'href',
      '/reportar/perdido',
    );
    expect(screen.getByRole('link', { name: '🔎 Buscar por descripción' })).toHaveAttribute(
      'href',
      '/buscar',
    );
    expect(screen.getByRole('link', { name: 'Ver el mapa' })).toHaveAttribute('href', '/mapa');
  });
});
