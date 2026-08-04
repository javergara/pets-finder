import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Sponsorship, UserProfile } from '../api/types';
import { MiPerfil } from './MiPerfil';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerPerfil: vi.fn(), listarApadrinamientos: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function renderConRouter() {
  return render(
    <MemoryRouter>
      <MiPerfil />
    </MemoryRouter>,
  );
}

const PERFIL_BASE: UserProfile = {
  id: 1,
  nombre: 'Ana Martínez',
  email: 'ana@example.com',
  ciudad: 'Bogotá',
  barrio: 'Chapinero',
  lat: null,
  lng: null,
  avatar_url: null,
  bio: 'Amo los animales y tengo experiencia con perros grandes.',
  creado_en: '2025-03-15T00:00:00Z',
  home_profile: {
    vivienda: 'casa',
    espacio_exterior: 'jardin',
    personas_en_casa: 3,
    tiene_ninos: true,
    tiene_otros_perros: false,
    tiene_otros_gatos: true,
    horas_fuera_dia: 6,
    experiencia_previa: 'mucha',
    presupuesto_mensual_cop: 300000,
    preferencia_especies: ['perro'],
    preferencia_tamanos: ['grande'],
    preferencia_energia: 'media',
  },
  metricas: {
    matches_activos: 4,
    visitas_agendadas: 1,
    apadrinamientos: 0,
  },
};

const APADRINAMIENTO_BASE: Sponsorship = {
  id: 1,
  pet: { id: 10, nombre: 'Rocky', fotos: ['/media/rocky.jpg'] },
  monto_cop: 70000,
  periodicidad: 'mensual',
  activo: true,
  iniciado_en: '2025-06-01T00:00:00Z',
  novedad:
    '¡Rocky está mejor gracias a tu ayuda! Este mes comió bien y tuvo su chequeo veterinario.',
};

describe('MiPerfil', () => {
  it('muestra cabecera, métricas, hogar y bio con un perfil completo', async () => {
    vi.mocked(client.obtenerPerfil).mockResolvedValue(PERFIL_BASE);
    vi.mocked(client.listarApadrinamientos).mockResolvedValue([]);

    renderConRouter();

    expect(await screen.findByText('Ana Martínez')).toBeInTheDocument();
    expect(screen.getByText(/Bogotá · Chapinero/)).toBeInTheDocument();

    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('Matches activos')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('Visitas agendadas')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('Apadrinamientos')).toBeInTheDocument();

    expect(screen.getByText('Jardín')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getAllByText('Sí')).toHaveLength(2); // tiene_ninos + tiene_otros_gatos
    expect(screen.getByText('6h')).toBeInTheDocument();

    expect(
      screen.getByText('Amo los animales y tengo experiencia con perros grandes.'),
    ).toBeInTheDocument();

    const link = screen.getByRole('link', { name: 'Editar cuestionario' });
    expect(link).toHaveAttribute('href', '/cuestionario');
  });

  it('muestra un placeholder de hogar cuando home_profile es null, sin romper, con link para completarlo', async () => {
    vi.mocked(client.obtenerPerfil).mockResolvedValue({
      ...PERFIL_BASE,
      home_profile: null,
    });
    vi.mocked(client.listarApadrinamientos).mockResolvedValue([]);

    renderConRouter();

    expect(await screen.findByText('Ana Martínez')).toBeInTheDocument();
    expect(
      screen.getByText(
        'Aún no completaste el cuestionario de hogar. Cuando lo hagas, aquí verás un resumen.',
      ),
    ).toBeInTheDocument();

    const link = screen.getByRole('link', { name: 'Completar cuestionario' });
    expect(link).toHaveAttribute('href', '/cuestionario');
  });

  it('muestra un estado vacío con link a /apadrinar cuando no hay apadrinamientos', async () => {
    vi.mocked(client.obtenerPerfil).mockResolvedValue(PERFIL_BASE);
    vi.mocked(client.listarApadrinamientos).mockResolvedValue([]);

    renderConRouter();

    expect(await screen.findByText('Ana Martínez')).toBeInTheDocument();
    expect(screen.getByText(/Todavía no apadrinas ninguna mascota\./)).toBeInTheDocument();

    const link = screen.getByRole('link', { name: 'Apadrina una ahora' });
    expect(link).toHaveAttribute('href', '/apadrinar');
  });

  it('muestra la mascota, el monto formateado, la periodicidad y la novedad de un apadrinamiento activo', async () => {
    vi.mocked(client.obtenerPerfil).mockResolvedValue(PERFIL_BASE);
    vi.mocked(client.listarApadrinamientos).mockResolvedValue([APADRINAMIENTO_BASE]);

    renderConRouter();

    expect(await screen.findByText('Rocky')).toBeInTheDocument();
    expect(screen.getByText('$70.000 · Mensual')).toBeInTheDocument();
    expect(
      screen.getByText(
        '¡Rocky está mejor gracias a tu ayuda! Este mes comió bien y tuvo su chequeo veterinario.',
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText('Inactivo')).not.toBeInTheDocument();
  });
});
