import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { HomeProfile, UserProfile } from '../api/types';
import { DEMO_USER_ID } from '../lib/constants';
import { RequiereHomeProfile } from './RequiereHomeProfile';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerPerfil: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function crearHomeProfile(): HomeProfile {
  return {
    vivienda: 'apartamento',
    espacio_exterior: 'ninguno',
    personas_en_casa: 2,
    tiene_ninos: false,
    tiene_otros_perros: false,
    tiene_otros_gatos: false,
    horas_fuera_dia: 6,
    experiencia_previa: 'con_experiencia',
    presupuesto_mensual_cop: 200000,
    preferencia_especies: ['perro'],
    preferencia_tamanos: ['mediano'],
    preferencia_energia: 'media',
  };
}

function crearPerfil(homeProfile: HomeProfile | null): UserProfile {
  return {
    id: DEMO_USER_ID,
    nombre: 'Ana Martínez',
    email: 'ana@example.com',
    ciudad: 'Bogotá',
    barrio: 'Chapinero',
    lat: null,
    lng: null,
    avatar_url: null,
    bio: null,
    creado_en: '2026-01-01T00:00:00Z',
    home_profile: homeProfile,
    metricas: { matches_activos: 0, visitas_agendadas: 0, apadrinamientos: 0 },
  };
}

function renderConRouter() {
  return render(
    <MemoryRouter initialEntries={['/descubrir']}>
      <Routes>
        <Route path="/cuestionario" element={<div>Cuestionario stub</div>} />
        <Route element={<RequiereHomeProfile />}>
          <Route path="/descubrir" element={<div>Descubrir stub</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe('RequiereHomeProfile', () => {
  it('sin HomeProfile, redirige a /cuestionario y no renderiza la ruta protegida', async () => {
    vi.mocked(client.obtenerPerfil).mockResolvedValue(crearPerfil(null));

    renderConRouter();

    await screen.findByText('Cuestionario stub');
    expect(screen.queryByText('Descubrir stub')).not.toBeInTheDocument();
  });

  it('con HomeProfile existente (usuario semilla), renderiza la ruta protegida sin redirigir', async () => {
    vi.mocked(client.obtenerPerfil).mockResolvedValue(crearPerfil(crearHomeProfile()));

    renderConRouter();

    await screen.findByText('Descubrir stub');
    expect(screen.queryByText('Cuestionario stub')).not.toBeInTheDocument();
  });

  it('si obtenerPerfil falla por un error real (no falta de HomeProfile), muestra un mensaje de error y no redirige a /cuestionario', async () => {
    vi.mocked(client.obtenerPerfil).mockRejectedValue(new client.ApiError('Error de red (500)'));

    renderConRouter();

    await screen.findByText('No pudimos cargar tu perfil. Intenta de nuevo en unos minutos.');
    expect(screen.queryByText('Cuestionario stub')).not.toBeInTheDocument();
    expect(screen.queryByText('Descubrir stub')).not.toBeInTheDocument();
  });
});
