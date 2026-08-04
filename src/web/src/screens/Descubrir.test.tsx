import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import { FILTROS_DEFAULT, type Pet } from '../api/types';
import { DEMO_USER_ID } from '../lib/constants';
import { Descubrir } from './Descubrir';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    listarMascotas: vi.fn(),
    registrarSwipe: vi.fn(),
    marcarFavorito: vi.fn(),
    desmarcarFavorito: vi.fn(),
  };
});

afterEach(() => {
  vi.resetAllMocks();
});

function crearMascota(id: number, nombre: string): Pet {
  return {
    id,
    shelter_id: 1,
    nombre,
    especie: 'perro',
    raza: 'Cocker mestizo',
    sexo: 'hembra',
    edad_meses: 42,
    tamano: 'mediano',
    energia: 'media',
    fotos: [],
    historia: '',
    tags: [],
    esterilizado: true,
    vacunas_al_dia: true,
    microchip: true,
    desparasitado: true,
    apto_ninos: true,
    apto_perros: true,
    apto_gatos: true,
    estado: 'disponible',
    publicado_en: '2026-01-01T00:00:00Z',
    shelter: null,
    afinidad: { score: 90, explicacion: '', incompatible: false },
    es_favorito: false,
    lat: null,
    lng: null,
    distancia_km: null,
  };
}

function renderConRouter() {
  return render(
    <MemoryRouter>
      <Descubrir />
    </MemoryRouter>,
  );
}

describe('Descubrir', () => {
  it('al montar, pide las mascotas con el usuario demo y los filtros por defecto', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([crearMascota(1, 'Canela')]);

    renderConRouter();

    await screen.findByText('Canela');

    expect(client.listarMascotas).toHaveBeenCalledWith(DEMO_USER_ID, FILTROS_DEFAULT);
  });

  it('el contador refleja la cantidad de mascotas devueltas', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([
      crearMascota(1, 'Canela'),
      crearMascota(2, 'Rocky'),
    ]);

    renderConRouter();

    expect(await screen.findByText('2 perfiles cerca de ti')).toBeInTheDocument();
  });

  it('cambiar un filtro (chip de especie) dispara un nuevo fetch con los params actualizados', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([crearMascota(1, 'Canela')]);

    renderConRouter();

    await screen.findByText('Canela');
    expect(client.listarMascotas).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText('Perro'));

    expect(client.listarMascotas).toHaveBeenCalledTimes(2);
    expect(client.listarMascotas).toHaveBeenLastCalledWith(DEMO_USER_ID, {
      ...FILTROS_DEFAULT,
      especie: ['perro'],
    });
  });

  it('clic en "Restablecer filtros" vuelve a llamar con los valores por defecto', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([crearMascota(1, 'Canela')]);

    renderConRouter();

    await screen.findByText('Canela');
    fireEvent.click(screen.getByText('Perro'));
    expect(client.listarMascotas).toHaveBeenCalledTimes(2);

    fireEvent.click(screen.getByText('Restablecer filtros'));

    expect(client.listarMascotas).toHaveBeenCalledTimes(3);
    expect(client.listarMascotas).toHaveBeenLastCalledWith(DEMO_USER_ID, FILTROS_DEFAULT);
  });

  it('el swipe optimista no dispara un refetch innecesario (mismos filtros)', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([
      crearMascota(1, 'Canela'),
      crearMascota(2, 'Rocky'),
    ]);
    vi.mocked(client.registrarSwipe).mockResolvedValue({
      id: 1,
      user_id: DEMO_USER_ID,
      pet_id: 1,
      direccion: 'like',
      creado_en: '2026-01-01T00:00:00Z',
      match: null,
    });

    renderConRouter();

    await screen.findByText('Canela');
    expect(client.listarMascotas).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByLabelText('Me interesa'));

    await screen.findByText('Rocky');
    expect(client.listarMascotas).toHaveBeenCalledTimes(1);
  });

  it('favoritear la carta actual no la remueve del array (a diferencia del swipe)', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([
      crearMascota(1, 'Canela'),
      crearMascota(2, 'Rocky'),
    ]);
    vi.mocked(client.marcarFavorito).mockResolvedValue(crearMascota(1, 'Canela'));

    renderConRouter();

    await screen.findByText('Canela');

    fireEvent.click(screen.getByLabelText('Guardar en favoritos'));

    expect(client.marcarFavorito).toHaveBeenCalledWith(DEMO_USER_ID, 1);
    // La carta sigue siendo la misma (no se quitó del array como sí hace el swipe).
    expect(screen.getByText('Canela')).toBeInTheDocument();
    expect(await screen.findByLabelText('Quitar de favoritos')).toBeInTheDocument();
  });
});
