import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { ShelterMap, UserProfile } from '../api/types';
import { posicionEnMapa } from '../lib/mapa';
import { Mapa } from './Mapa';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, listarRefugiosMapa: vi.fn(), obtenerPerfil: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function renderConRouter() {
  return render(
    <MemoryRouter>
      <Mapa />
    </MemoryRouter>,
  );
}

const PERFIL_BASE: UserProfile = {
  id: 1,
  nombre: 'Ana Martínez',
  email: 'ana@example.com',
  ciudad: 'Bogotá',
  barrio: 'Chapinero',
  lat: 4.675,
  lng: -74.1,
  avatar_url: null,
  bio: null,
  creado_en: '2025-03-15T00:00:00Z',
  home_profile: null,
  metricas: null,
};

const REFUGIO_VERIFICADO: ShelterMap = {
  id: 1,
  nombre: 'Refugio Patitas',
  verificado: true,
  lat: 4.675,
  lng: -74.1,
  mascotas_disponibles: 2,
  mascotas: [
    { id: 10, nombre: 'Canela', fotos: ['/media/canela.jpg'] },
    { id: 11, nombre: 'Rocky', fotos: [] },
  ],
  distancia_km: 3.456,
};

const REFUGIO_SIN_VERIFICAR: ShelterMap = {
  id: 2,
  nombre: 'Huellitas Bogotá',
  verificado: false,
  lat: 4.8,
  lng: -74.2,
  mascotas_disponibles: 0,
  mascotas: [],
  distancia_km: null,
};

const REFUGIO_SIN_COORDENADAS: ShelterMap = {
  id: 3,
  nombre: 'Refugio Sin Ubicación',
  verificado: false,
  lat: null,
  lng: null,
  mascotas_disponibles: 0,
  mascotas: [],
  distancia_km: null,
};

describe('Mapa', () => {
  it('muestra el skeleton de carga antes de que resuelvan las promesas', () => {
    vi.mocked(client.listarRefugiosMapa).mockReturnValue(new Promise(() => {}));
    vi.mocked(client.obtenerPerfil).mockReturnValue(new Promise(() => {}));

    const { container } = renderConRouter();

    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('posiciona cada pin según posicionEnMapa con las coordenadas del refugio', async () => {
    vi.mocked(client.listarRefugiosMapa).mockResolvedValue([
      REFUGIO_VERIFICADO,
      REFUGIO_SIN_VERIFICAR,
    ]);
    vi.mocked(client.obtenerPerfil).mockResolvedValue(PERFIL_BASE);

    renderConRouter();

    const pin1 = await screen.findByTestId('pin-refugio-1');
    const esperado1 = posicionEnMapa(
      REFUGIO_VERIFICADO.lat as number,
      REFUGIO_VERIFICADO.lng as number,
    );
    expect(pin1.style.left).toBe(esperado1.left);
    expect(pin1.style.top).toBe(esperado1.top);

    const pin2 = await screen.findByTestId('pin-refugio-2');
    const esperado2 = posicionEnMapa(
      REFUGIO_SIN_VERIFICAR.lat as number,
      REFUGIO_SIN_VERIFICAR.lng as number,
    );
    expect(pin2.style.left).toBe(esperado2.left);
    expect(pin2.style.top).toBe(esperado2.top);
  });

  it('no renderiza pin para un refugio con lat/lng null', async () => {
    vi.mocked(client.listarRefugiosMapa).mockResolvedValue([
      REFUGIO_VERIFICADO,
      REFUGIO_SIN_COORDENADAS,
    ]);
    vi.mocked(client.obtenerPerfil).mockResolvedValue(PERFIL_BASE);

    renderConRouter();

    await screen.findByTestId('pin-refugio-1');
    expect(screen.queryByTestId('pin-refugio-3')).not.toBeInTheDocument();
  });

  it('click en un pin abre el panel con nombre, insignia de verificado, distancia y mascotas', async () => {
    vi.mocked(client.listarRefugiosMapa).mockResolvedValue([REFUGIO_VERIFICADO]);
    vi.mocked(client.obtenerPerfil).mockResolvedValue(PERFIL_BASE);

    renderConRouter();

    fireEvent.click(await screen.findByTestId('pin-refugio-1'));

    expect(await screen.findByText('Refugio Patitas')).toBeInTheDocument();
    expect(screen.getByText('Verificado')).toBeInTheDocument();
    expect(screen.getByText('3.5 km')).toBeInTheDocument();

    const enlaceCanela = screen.getByRole('link', { name: /canela/i });
    expect(enlaceCanela).toHaveAttribute('href', '/mascota/10');
    const enlaceRocky = screen.getByRole('link', { name: /rocky/i });
    expect(enlaceRocky).toHaveAttribute('href', '/mascota/11');
  });

  it('un refugio sin mascotas muestra el mensaje correspondiente sin ocultar el panel', async () => {
    vi.mocked(client.listarRefugiosMapa).mockResolvedValue([REFUGIO_SIN_VERIFICAR]);
    vi.mocked(client.obtenerPerfil).mockResolvedValue(PERFIL_BASE);

    renderConRouter();

    fireEvent.click(await screen.findByTestId('pin-refugio-2'));

    expect(await screen.findByText('Huellitas Bogotá')).toBeInTheDocument();
    expect(screen.queryByText('Verificado')).not.toBeInTheDocument();
    expect(screen.getByText('Sin mascotas disponibles ahora mismo.')).toBeInTheDocument();
  });

  it('sin refugio seleccionado muestra el mensaje de selección', async () => {
    vi.mocked(client.listarRefugiosMapa).mockResolvedValue([REFUGIO_VERIFICADO]);
    vi.mocked(client.obtenerPerfil).mockResolvedValue(PERFIL_BASE);

    renderConRouter();

    await screen.findByTestId('pin-refugio-1');
    expect(
      screen.getByText('Selecciona un refugio en el mapa para ver sus mascotas.'),
    ).toBeInTheDocument();
  });
});
