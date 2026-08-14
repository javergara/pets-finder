import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import { LandingEmergencia } from './LandingEmergencia';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerReunidos: vi.fn(), obtenerConteos: vi.fn() };
});

beforeEach(() => {
  vi.mocked(client.obtenerReunidos).mockResolvedValue({ total: 0, recientes: [] });
  vi.mocked(client.obtenerConteos).mockResolvedValue({ perdidos: 0, encontrados: 0 });
});

afterEach(() => {
  vi.resetAllMocks();
});

function renderLanding() {
  return render(
    <MemoryRouter>
      <LandingEmergencia />
    </MemoryRouter>,
  );
}

describe('LandingEmergencia', () => {
  it('muestra los dos CTAs gigantes con sus destinos', () => {
    renderLanding();

    expect(screen.getByRole('link', { name: 'Perdí a mi mascota' })).toHaveAttribute(
      'href',
      '/reportar/perdido',
    );
    expect(screen.getByRole('link', { name: 'Encontré una mascota' })).toHaveAttribute(
      'href',
      '/reportar/encontrado',
    );
  });

  it('da acceso al listado y al mapa como botones visibles (feature 35)', () => {
    renderLanding();

    const reportes = screen.getByRole('link', { name: 'Ver todos los reportes' });
    expect(reportes).toHaveAttribute('href', '/reportes');
    // Botón con borde, no link subrayado: visibilidad sin competir con los CTAs.
    expect(reportes.className).toContain('border-forest');
    expect(screen.getByRole('link', { name: 'Ver el mapa' })).toHaveAttribute('href', '/mapa');
  });

  it('da acceso a la búsqueda por descripción (feature 38)', () => {
    renderLanding();

    expect(
      screen.getByRole('link', { name: '🔎 Busca a tu mascota por descripción' }),
    ).toHaveAttribute('href', '/buscar');
  });

  it('muestra el logo oficial y el acceso a los centros de ayuda', () => {
    renderLanding();

    expect(screen.getByAltText('Pet Finder Col')).toHaveAttribute('src', '/logo.svg');
    expect(
      screen.getByRole('link', { name: 'Centros de ayuda: acopio, fundaciones y donaciones' }),
    ).toHaveAttribute('href', '/ayudar');
  });

  it('nombra las zonas cubiertas incluyendo Cali y Quibdó', () => {
    renderLanding();

    expect(
      screen.getByText(/Armenia · Pereira · Manizales · Cali · Quibdó · Bogotá/),
    ).toBeInTheDocument();
  });

  it('muestra la franja de reencuentros con el contador y la mini-galería', async () => {
    vi.mocked(client.obtenerReunidos).mockResolvedValue({
      total: 2,
      recientes: [
        {
          id: 16,
          user_id: 1,
          tipo: 'perdido',
          especie: 'perro',
          nombre_mascota: 'Firulais',
          raza: null,
          color: null,
          tamano: null,
          descripcion: 'd',
          foto_url: '/media/seed/report_16.jpg',
          zona: 'Armenia',
          ciudad_texto: null,
          barrio: null,
          lat: 4.55,
          lng: -75.69,
          situacion: null,
          fecha_evento: '2026-08-10',
          telefono_contacto: '300',
          instagram: null,
          facebook: null,
          fuente: 'manual',
          crawl_metadata: null,
          idempotency_id: null,
          estado: 'reunido',
          resuelto_en: '2026-08-12T15:00:00',
          creado_en: '2026-08-12T08:00:00',
        },
      ],
    });

    renderLanding();

    expect(await screen.findByText('2')).toBeInTheDocument();
    expect(screen.getByText('reencuentros logrados gracias a la comunidad')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Reencuentro de Firulais' })).toHaveAttribute(
      'href',
      '/reporte/16',
    );
  });

  it('sin reencuentros no muestra la franja (y la landing no se bloquea)', async () => {
    renderLanding();

    // Los CTAs están de inmediato; la franja nunca aparece con total 0.
    expect(screen.getByRole('link', { name: 'Perdí a mi mascota' })).toBeInTheDocument();
    expect(screen.queryByText(/reencuentros logrados/)).not.toBeInTheDocument();
  });

  it('muestra la dimensión del problema con los conteos del backend', async () => {
    vi.mocked(client.obtenerConteos).mockResolvedValue({ perdidos: 12, encontrados: 5 });

    renderLanding();

    expect(await screen.findByText('12 mascotas perdidas')).toBeInTheDocument();
    expect(screen.getByText('5 encontradas')).toBeInTheDocument();
  });

  it('la franja enlaza a la vista completa de reencuentros', async () => {
    vi.mocked(client.obtenerReunidos).mockResolvedValue({ total: 3, recientes: [] });

    renderLanding();

    expect(await screen.findByRole('link', { name: 'Ver todos los reencuentros' })).toHaveAttribute(
      'href',
      '/reportes?estado=reunido',
    );
  });
});
