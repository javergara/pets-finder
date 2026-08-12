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
    ciudad: 'Armenia',
    barrio: 'La Castellana',
    lat: null,
    lng: null,
    avatar_url: null,
    bio: null,
    creado_en: '2026-08-11T00:00:00Z',
  };
}

function renderConRouter(entrada = '/registro') {
  return render(
    <MemoryRouter initialEntries={[entrada]}>
      <Routes>
        <Route path="/registro" element={<Registro />} />
        <Route path="/" element={<div>Landing stub</div>} />
        <Route path="/reportar/perdido" element={<div>Reportar perdido stub</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function llenarFormulario() {
  fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Ana Martínez' } });
  fireEvent.change(screen.getByLabelText('Correo'), { target: { value: 'ana@example.com' } });
  fireEvent.change(screen.getByLabelText('Ciudad'), { target: { value: 'Armenia' } });
  fireEvent.change(screen.getByLabelText('Barrio (opcional)'), {
    target: { value: 'La Castellana' },
  });
}

describe('Registro', () => {
  it('al completar el formulario y enviar, registra al usuario, guarda su id activo y navega a "/"', async () => {
    const setActiveUserIdSpy = vi.spyOn(session, 'setActiveUserId');
    vi.mocked(client.registrarUsuario).mockResolvedValue(crearPerfil(42));

    renderConRouter();
    llenarFormulario();
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    await screen.findByText('Landing stub');

    expect(client.registrarUsuario).toHaveBeenCalledWith({
      nombre: 'Ana Martínez',
      email: 'ana@example.com',
      ciudad: 'Armenia',
      barrio: 'La Castellana',
    });
    expect(setActiveUserIdSpy).toHaveBeenCalledWith(42);
  });

  it('con ?volver=/reportar/perdido, tras registrarse vuelve al formulario de reporte', async () => {
    vi.mocked(client.registrarUsuario).mockResolvedValue(crearPerfil(7));

    renderConRouter('/registro?volver=/reportar/perdido');
    llenarFormulario();
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    await screen.findByText('Reportar perdido stub');
  });

  it('un ?volver= externo (URL absoluta) se ignora y navega a "/"', async () => {
    vi.mocked(client.registrarUsuario).mockResolvedValue(crearPerfil(8));

    renderConRouter('/registro?volver=https://evil.example.com');
    llenarFormulario();
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    await screen.findByText('Landing stub');
  });

  it('si el correo ya está registrado, muestra el mensaje del backend y no navega', async () => {
    vi.mocked(client.registrarUsuario).mockRejectedValue(
      new client.ApiError('Ya existe una cuenta con el correo ana@example.com'),
    );

    renderConRouter();
    llenarFormulario();
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));

    await screen.findByText('Ya existe una cuenta con el correo ana@example.com');

    expect(screen.queryByText('Landing stub')).not.toBeInTheDocument();
  });
});
