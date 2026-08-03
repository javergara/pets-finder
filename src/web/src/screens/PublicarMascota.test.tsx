import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Pet } from '../api/types';
import { DEMO_SHELTER_ID } from '../lib/constants';
import { PublicarMascota } from './PublicarMascota';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, publicarMascota: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function renderConRouter() {
  return render(
    <MemoryRouter initialEntries={['/refugio/publicar']}>
      <Routes>
        <Route path="/refugio/publicar" element={<PublicarMascota />} />
        <Route path="/refugio" element={<div>Panel del refugio stub</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function llenarFormulario() {
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Canela' } });
  fireEvent.click(screen.getByRole('button', { name: 'Perro' }));
  fireEvent.change(screen.getByLabelText('Raza'), { target: { value: 'Cocker mestizo' } });
  fireEvent.click(screen.getByRole('button', { name: 'Hembra' }));
  fireEvent.change(screen.getByLabelText('Edad (meses)'), { target: { value: '24' } });
  fireEvent.click(screen.getByRole('button', { name: 'Mediano' }));
  fireEvent.click(screen.getByRole('button', { name: 'Alta' }));
  fireEvent.change(screen.getByLabelText('Historia'), {
    target: { value: 'Canela llegó al refugio hace un mes y busca un hogar tranquilo.' },
  });
}

const MASCOTA_CREADA = { id: 99 } as Pet;

describe('PublicarMascota', () => {
  it('al completar el formulario y enviar, publica la mascota con el payload correcto y navega a /refugio', async () => {
    vi.mocked(client.publicarMascota).mockResolvedValue(MASCOTA_CREADA);

    renderConRouter();
    llenarFormulario();
    fireEvent.click(screen.getByRole('button', { name: 'Publicar mascota' }));

    await screen.findByText('Panel del refugio stub');

    expect(client.publicarMascota).toHaveBeenCalledWith({
      shelter_id: DEMO_SHELTER_ID,
      nombre: 'Canela',
      especie: 'perro',
      raza: 'Cocker mestizo',
      sexo: 'hembra',
      edad_meses: 24,
      tamano: 'mediano',
      energia: 'alta',
      historia: 'Canela llegó al refugio hace un mes y busca un hogar tranquilo.',
      tags: [],
      esterilizado: false,
      vacunas_al_dia: false,
      microchip: false,
      desparasitado: false,
      apto_ninos: true,
      apto_perros: true,
      apto_gatos: true,
    });
  });

  it('si el backend rechaza la publicación, muestra el mensaje del backend y no navega', async () => {
    vi.mocked(client.publicarMascota).mockRejectedValue(
      new client.ApiError('No existe un refugio con id 1'),
    );

    renderConRouter();
    llenarFormulario();
    fireEvent.click(screen.getByRole('button', { name: 'Publicar mascota' }));

    await screen.findByText('No existe un refugio con id 1');

    expect(screen.queryByText('Panel del refugio stub')).not.toBeInTheDocument();
  });
});
