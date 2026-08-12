import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import { ZONAS } from '../lib/ciudades';
import { setActiveUserId } from '../lib/session';
import { RegistrarOrganizacion } from './RegistrarOrganizacion';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, crearOrganizacion: vi.fn() };
});

beforeEach(() => {
  // El gate mira localStorage: con esto el usuario "existe".
  setActiveUserId(1);
});

afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
});

function renderRegistrar() {
  return render(
    <MemoryRouter initialEntries={['/ayudar/registrar']}>
      <Routes>
        <Route path="/ayudar/registrar" element={<RegistrarOrganizacion />} />
        <Route path="/registro" element={<div>Registro stub</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('RegistrarOrganizacion', () => {
  it('sin usuario activo redirige a /registro con ?volver=', async () => {
    localStorage.clear();

    renderRegistrar();

    expect(await screen.findByText('Registro stub')).toBeInTheDocument();
  });

  it('envía el payload completo con el pin en el centro de la zona elegida', async () => {
    vi.mocked(client.crearOrganizacion).mockResolvedValue({
      id: 7,
      user_id: 1,
      tipo: 'centro_acopio',
      nombre: 'Acopio Parque Sucre',
      descripcion: 'Recibimos alimento y cobijas',
      zona: 'Medellín',
      ciudad_texto: null,
      barrio: null,
      direccion: 'Parque Sucre',
      lat: ZONAS.Medellín.centroLat,
      lng: ZONAS.Medellín.centroLng,
      telefono_contacto: '3001112233',
      horario: '24 horas',
      como_donar: null,
      foto_url: null,
      estado: 'activo',
      creado_en: '2026-08-12T10:00:00',
    });

    renderRegistrar();

    fireEvent.change(screen.getByLabelText('Tipo de lugar'), {
      target: { value: 'centro_acopio' },
    });
    fireEvent.change(screen.getByLabelText('Nombre'), {
      target: { value: 'Acopio Parque Sucre' },
    });
    fireEvent.change(screen.getByLabelText('Qué hacen / qué reciben'), {
      target: { value: 'Recibimos alimento y cobijas' },
    });
    fireEvent.change(screen.getByLabelText('Zona'), { target: { value: 'Medellín' } });
    fireEvent.change(screen.getByLabelText('Dirección'), { target: { value: 'Parque Sucre' } });
    fireEvent.change(screen.getByLabelText('Teléfono / WhatsApp'), {
      target: { value: '3001112233' },
    });
    fireEvent.change(screen.getByLabelText('Horario (opcional)'), {
      target: { value: '24 horas' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Registrar lugar' }));

    expect(await screen.findByText('¡Lugar registrado! 💚')).toBeInTheDocument();
    expect(client.crearOrganizacion).toHaveBeenCalledWith(
      expect.objectContaining({
        user_id: 1,
        tipo: 'centro_acopio',
        nombre: 'Acopio Parque Sucre',
        zona: 'Medellín',
        direccion: 'Parque Sucre',
        telefono_contacto: '3001112233',
        horario: '24 horas',
        // Sin click en el mapa el pin queda en el centro de la zona.
        lat: ZONAS.Medellín.centroLat,
        lng: ZONAS.Medellín.centroLng,
      }),
    );
    expect(screen.getByRole('link', { name: 'Ver su página' })).toHaveAttribute(
      'href',
      '/organizacion/7',
    );
  });

  it('valida los obligatorios antes de llamar al API', async () => {
    renderRegistrar();

    fireEvent.click(screen.getByRole('button', { name: 'Registrar lugar' }));

    expect(
      await screen.findByText('Nombre, descripción, dirección y teléfono son obligatorios.'),
    ).toBeInTheDocument();
    expect(client.crearOrganizacion).not.toHaveBeenCalled();
  });
});
