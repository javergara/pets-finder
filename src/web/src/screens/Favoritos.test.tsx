import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Pet } from '../api/types';
import { Favoritos } from './Favoritos';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, listarFavoritos: vi.fn(), desmarcarFavorito: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function renderConRouter() {
  return render(
    <MemoryRouter>
      <Favoritos />
    </MemoryRouter>,
  );
}

const PET_BASE: Pet = {
  id: 17,
  shelter_id: 1,
  nombre: 'Canela',
  especie: 'perro',
  raza: 'Cocker mestizo',
  sexo: 'hembra',
  edad_meses: 42,
  tamano: 'mediano',
  energia: 'media',
  fotos: ['/media/canela.jpg'],
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
  afinidad: { score: 94, explicacion: '', incompatible: false },
  es_favorito: true,
  lat: null,
  lng: null,
  distancia_km: null,
};

describe('Favoritos', () => {
  it('muestra el skeleton de carga antes de que resuelva la promesa', () => {
    vi.mocked(client.listarFavoritos).mockReturnValue(new Promise(() => {}));

    const { container } = renderConRouter();

    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('muestra el estado vacío con un enlace a Descubrir cuando no hay favoritos', async () => {
    vi.mocked(client.listarFavoritos).mockResolvedValue([]);

    renderConRouter();

    expect(await screen.findByText('Aún no tienes favoritos')).toBeInTheDocument();
    const enlace = screen.getByRole('link', { name: /ir a descubrir/i });
    expect(enlace).toHaveAttribute('href', '/descubrir');
  });

  it('lista los favoritos con foto, nombre y afinidad cuando sí hay', async () => {
    vi.mocked(client.listarFavoritos).mockResolvedValue([PET_BASE]);

    renderConRouter();

    expect(await screen.findByText('Canela')).toBeInTheDocument();
    expect(screen.getByText('94%')).toBeInTheDocument();
    const enlace = screen.getByRole('link', { name: /canela/i });
    expect(enlace).toHaveAttribute('href', '/mascota/17');
  });

  it('maneja afinidad null sin romper (el backend no la calcula en este endpoint)', async () => {
    vi.mocked(client.listarFavoritos).mockResolvedValue([{ ...PET_BASE, afinidad: null }]);

    renderConRouter();

    expect(await screen.findByText('Canela')).toBeInTheDocument();
    expect(screen.queryByText('94%')).not.toBeInTheDocument();
  });

  it('quitar de favoritos llama a desmarcarFavorito con los ids correctos y remueve la tarjeta', async () => {
    vi.mocked(client.listarFavoritos).mockResolvedValue([PET_BASE]);
    vi.mocked(client.desmarcarFavorito).mockResolvedValue(undefined);

    renderConRouter();
    await screen.findByText('Canela');

    fireEvent.click(screen.getByRole('button', { name: 'Quitar de favoritos' }));

    expect(client.desmarcarFavorito).toHaveBeenCalledWith(1, 17);
    expect(await screen.findByText('Aún no tienes favoritos')).toBeInTheDocument();
  });
});
