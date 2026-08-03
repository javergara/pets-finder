import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { UserProfile } from '../api/types';
import { MiPerfil } from './MiPerfil';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerPerfil: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

const PERFIL_BASE: UserProfile = {
  id: 1,
  nombre: 'Ana Martínez',
  email: 'ana@example.com',
  ciudad: 'Bogotá',
  barrio: 'Chapinero',
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

describe('MiPerfil', () => {
  it('muestra cabecera, métricas, hogar y bio con un perfil completo', async () => {
    vi.mocked(client.obtenerPerfil).mockResolvedValue(PERFIL_BASE);

    render(<MiPerfil />);

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
  });

  it('muestra un placeholder de hogar cuando home_profile es null, sin romper', async () => {
    vi.mocked(client.obtenerPerfil).mockResolvedValue({
      ...PERFIL_BASE,
      home_profile: null,
    });

    render(<MiPerfil />);

    expect(await screen.findByText('Ana Martínez')).toBeInTheDocument();
    expect(
      screen.getByText(
        'Aún no completaste el cuestionario de hogar. Cuando lo hagas, aquí verás un resumen.',
      ),
    ).toBeInTheDocument();
  });
});
