import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { HomeProfile, UserProfile } from '../api/types';
import { Cuestionario } from './Cuestionario';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    obtenerPerfil: vi.fn(),
    guardarHomeProfile: vi.fn(),
  };
});

afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
});

function crearPerfil(homeProfile: HomeProfile | null): UserProfile {
  return {
    id: 1,
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

const HOME_PROFILE_EXISTENTE: HomeProfile = {
  vivienda: 'casa',
  espacio_exterior: 'jardin',
  personas_en_casa: 3,
  tiene_ninos: true,
  tiene_otros_perros: true,
  tiene_otros_gatos: false,
  horas_fuera_dia: 6,
  experiencia_previa: 'mucha',
  presupuesto_mensual_cop: 500000,
  preferencia_especies: ['perro'],
  preferencia_tamanos: ['grande'],
  preferencia_energia: 'alta',
};

function renderConRouter() {
  return render(
    <MemoryRouter initialEntries={['/cuestionario']}>
      <Routes>
        <Route path="/cuestionario" element={<Cuestionario />} />
        <Route path="/descubrir" element={<div>Descubrir stub</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('Cuestionario', () => {
  it('modo primera vez: completa los 6 pasos, guarda el payload acumulado y navega a /descubrir', async () => {
    vi.mocked(client.obtenerPerfil).mockResolvedValue(crearPerfil(null));
    vi.mocked(client.guardarHomeProfile).mockResolvedValue(HOME_PROFILE_EXISTENTE);

    renderConRouter();
    await screen.findByText('Paso 1 de 6');

    // Paso 1: vivienda + espacio exterior
    fireEvent.click(screen.getByRole('button', { name: 'Apartamento' }));
    fireEvent.click(screen.getByRole('button', { name: 'Patio' }));
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    // Paso 2: niños en casa (personas_en_casa se queda en el default 1)
    await screen.findByText('Paso 2 de 6');
    fireEvent.click(screen.getByRole('button', { name: 'No' }));
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    // Paso 3: horas fuera (se queda en el default 8)
    await screen.findByText('Paso 3 de 6');
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    // Paso 4: otras mascotas
    await screen.findByText('Paso 4 de 6');
    fireEvent.click(screen.getAllByRole('button', { name: 'Sí' })[0]);
    fireEvent.click(screen.getAllByRole('button', { name: 'No' })[1]);
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    // Paso 5: experiencia previa (presupuesto se queda en el default 300000)
    await screen.findByText('Paso 5 de 6');
    fireEvent.click(screen.getByRole('button', { name: 'Algo de experiencia' }));
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    // Paso 6: preferencias de compañía
    await screen.findByText('Paso 6 de 6');
    fireEvent.click(screen.getByRole('button', { name: 'Gato' }));
    fireEvent.click(screen.getByRole('button', { name: 'Mediano' }));
    fireEvent.click(screen.getByRole('button', { name: 'Media' }));
    fireEvent.click(screen.getByRole('button', { name: 'Terminar' }));

    await screen.findByText('Descubrir stub');

    expect(client.guardarHomeProfile).toHaveBeenCalledWith(1, {
      vivienda: 'apartamento',
      espacio_exterior: 'patio',
      personas_en_casa: 1,
      tiene_ninos: false,
      horas_fuera_dia: 8,
      tiene_otros_perros: true,
      tiene_otros_gatos: false,
      experiencia_previa: 'algo',
      presupuesto_mensual_cop: 300000,
      preferencia_especies: ['gato'],
      preferencia_tamanos: ['mediano'],
      preferencia_energia: 'media',
    });
  });

  it('modo edición: precarga las respuestas existentes en el paso 1', async () => {
    vi.mocked(client.obtenerPerfil).mockResolvedValue(crearPerfil(HOME_PROFILE_EXISTENTE));

    renderConRouter();

    expect(await screen.findByRole('button', { name: 'Casa', pressed: true })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Jardín', pressed: true })).toBeInTheDocument();
  });

  it('el botón Atrás no está disponible en el paso 1, y retrocede desde el paso 2 en adelante', async () => {
    vi.mocked(client.obtenerPerfil).mockResolvedValue(crearPerfil(null));

    renderConRouter();
    await screen.findByText('Paso 1 de 6');
    expect(screen.queryByRole('button', { name: 'Atrás' })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Apartamento' }));
    fireEvent.click(screen.getByRole('button', { name: 'Patio' }));
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    await screen.findByText('Paso 2 de 6');
    expect(screen.getByRole('button', { name: 'Atrás' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Atrás' }));

    await screen.findByText('Paso 1 de 6');
  });
});
