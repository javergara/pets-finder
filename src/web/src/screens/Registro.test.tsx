import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { UserProfile } from '../api/types';
import * as session from '../lib/session';
import { Registro } from './Registro';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, registrarUsuario: vi.fn() };
});

afterEach(() => {
  vi.resetAllMocks();
});

function crearPerfil(id: number): UserProfile {
  return {
    id,
    nombre: 'Ana Martínez',
    email: 'ana@example.com',
    ciudad: 'Bogotá',
    barrio: 'Chapinero',
    lat: null,
    lng: null,
    avatar_url: null,
    bio: null,
    creado_en: '2026-01-01T00:00:00Z',
    home_profile: null,
    metricas: { matches_activos: 0, visitas_agendadas: 0, apadrinamientos: 0 },
  };
}

function renderConRouter() {
  return render(
    <MemoryRouter initialEntries={['/registro']}>
      <Routes>
        <Route path="/registro" element={<Registro />} />
        <Route path="/cuestionario" element={<div>Cuestionario stub</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function llenarFormulario() {
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Ana Martínez' } });
  fireEvent.change(screen.getByLabelText('Correo'), { target: { value: 'ana@example.com' } });
  fireEvent.change(screen.getByLabelText('Ciudad'), { target: { value: 'Bogotá' } });
  fireEvent.change(screen.getByLabelText('Barrio (opcional)'), {
    target: { value: 'Chapinero' },
  });
}

describe('Registro', () => {
  it('al completar el formulario y enviar, registra al usuario, guarda su id activo y navega a /cuestionario', async () => {
    const setActiveUserIdSpy = vi.spyOn(session, 'setActiveUserId');
    vi.mocked(client.registrarUsuario).mockResolvedValue(crearPerfil(42));

    renderConRouter();
    llenarFormulario();
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    await screen.findByText('Cuestionario stub');

    expect(client.registrarUsuario).toHaveBeenCalledWith({
      nombre: 'Ana Martínez',
      email: 'ana@example.com',
      ciudad: 'Bogotá',
      barrio: 'Chapinero',
    });
    expect(setActiveUserIdSpy).toHaveBeenCalledWith(42);
  });

  it('si el correo ya está registrado, muestra el mensaje del backend y no navega', async () => {
    vi.mocked(client.registrarUsuario).mockRejectedValue(
      new client.ApiError('Ya existe una cuenta con el correo ana@example.com'),
    );

    renderConRouter();
    llenarFormulario();
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    await screen.findByText('Ya existe una cuenta con el correo ana@example.com');

    expect(screen.queryByText('Cuestionario stub')).not.toBeInTheDocument();
  });
});
