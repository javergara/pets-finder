import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Pet } from '../api/types';
import { MascotaDetalle } from './MascotaDetalle';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    obtenerMascota: vi.fn(),
    marcarFavorito: vi.fn(),
    desmarcarFavorito: vi.fn(),
  };
});

afterEach(() => {
  vi.resetAllMocks();
});

function renderConRouter(id = '17') {
  return render(
    <MemoryRouter initialEntries={[`/mascota/${id}`]}>
      <Routes>
        <Route path="/mascota/:id" element={<MascotaDetalle />} />
      </Routes>
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
  fotos: [],
  historia: 'Una perrita muy dulce.',
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
  afinidad: { score: 94, explicacion: 'Buena combinación.', incompatible: false },
  es_favorito: false,
  lat: null,
  lng: null,
  distancia_km: null,
};

describe('MascotaDetalle', () => {
  it('el botón de favorito arranca vacío y al pulsarlo llama a marcarFavorito y se actualiza a lleno', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue(PET_BASE);
    vi.mocked(client.marcarFavorito).mockResolvedValue({ ...PET_BASE, es_favorito: true });

    renderConRouter();

    const boton = await screen.findByLabelText('Guardar en favoritos');
    expect(boton).toHaveTextContent('♡');

    fireEvent.click(boton);

    expect(client.marcarFavorito).toHaveBeenCalledWith(1, 17);
    expect(await screen.findByLabelText('Quitar de favoritos')).toHaveTextContent('♥');
  });

  it('si la mascota ya es favorita, al pulsar el botón llama a desmarcarFavorito y se actualiza a vacío', async () => {
    vi.mocked(client.obtenerMascota).mockResolvedValue({ ...PET_BASE, es_favorito: true });
    vi.mocked(client.desmarcarFavorito).mockResolvedValue(undefined);

    renderConRouter();

    const boton = await screen.findByLabelText('Quitar de favoritos');
    expect(boton).toHaveTextContent('♥');

    fireEvent.click(boton);

    expect(client.desmarcarFavorito).toHaveBeenCalledWith(1, 17);
    expect(await screen.findByLabelText('Guardar en favoritos')).toHaveTextContent('♡');
  });
});
