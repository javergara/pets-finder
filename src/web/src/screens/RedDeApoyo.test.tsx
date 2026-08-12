import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Organizacion } from '../api/types';
import { RedDeApoyo } from './RedDeApoyo';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, listarOrganizaciones: vi.fn() };
});

beforeEach(() => {
  vi.mocked(client.listarOrganizaciones).mockResolvedValue([]);
});

afterEach(() => {
  vi.resetAllMocks();
});

function crearOrganizacion(overrides: Partial<Organizacion> = {}): Organizacion {
  return {
    id: 1,
    user_id: 1,
    tipo: 'fundacion',
    nombre: 'Fundación Huellitas',
    descripcion: 'Rescatamos mascotas afectadas por el sismo.',
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: 'Centro',
    direccion: 'Cra 14 #10-25',
    lat: 4.535,
    lng: -75.68,
    telefono_contacto: '3001112233',
    horario: 'Lun-Sáb 8am-5pm',
    como_donar: 'Nequi 3001112233',
    foto_url: null,
    estado: 'activo',
    creado_en: '2026-08-12T10:00:00',
    necesidades_pendientes: 0,
    ...overrides,
  };
}

function renderRed() {
  return render(
    <MemoryRouter initialEntries={['/ayudar']}>
      <RedDeApoyo />
    </MemoryRouter>,
  );
}

describe('RedDeApoyo', () => {
  it('muestra las tarjetas con nombre, tipo, dirección y horario, y el pin en el mapa', async () => {
    vi.mocked(client.listarOrganizaciones).mockResolvedValue([
      crearOrganizacion(),
      crearOrganizacion({
        id: 2,
        tipo: 'centro_acopio',
        nombre: 'Acopio Parque Sucre',
        direccion: 'Parque Sucre, Armenia',
        horario: '24 horas',
      }),
    ]);

    renderRed();

    expect(await screen.findByText('Fundación Huellitas')).toBeInTheDocument();
    expect(screen.getByText('Acopio Parque Sucre')).toBeInTheDocument();
    expect(screen.getByText(/Cra 14 #10-25/)).toBeInTheDocument();
    expect(screen.getByText('Lun-Sáb 8am-5pm')).toBeInTheDocument();

    // Pins accesibles con el color por tipo.
    const pinFundacion = screen.getByRole('button', { name: 'Fundación Huellitas (Fundación)' });
    expect(pinFundacion.className).toContain('bg-forest');
    const pinAcopio = screen.getByRole('button', {
      name: 'Acopio Parque Sucre (Centro de acopio)',
    });
    expect(pinAcopio.className).toContain('bg-ochre');

    // Cada tarjeta navega al detalle.
    const links = screen.getAllByRole('link');
    expect(links.some((l) => l.getAttribute('href') === '/organizacion/1')).toBe(true);
  });

  it('el chip de tipo re-consulta al backend con ese filtro', async () => {
    renderRed();
    await screen.findByText(/Aún no hay lugares/);

    fireEvent.click(screen.getByRole('button', { name: /Centro de acopio/ }));

    expect(client.listarOrganizaciones).toHaveBeenLastCalledWith({
      tipo: 'centro_acopio',
      zona: undefined,
    });
  });

  it('el selector de zona re-consulta al backend con esa zona', async () => {
    renderRed();
    await screen.findByText(/Aún no hay lugares/);

    fireEvent.change(screen.getByLabelText('Zona'), { target: { value: 'Medellín' } });

    expect(client.listarOrganizaciones).toHaveBeenLastCalledWith({
      tipo: undefined,
      zona: 'Medellín',
    });
  });

  it('las tarjetas muestran el contador de necesidades activas cuando hay', async () => {
    vi.mocked(client.listarOrganizaciones).mockResolvedValue([
      crearOrganizacion({ necesidades_pendientes: 3 }),
      crearOrganizacion({
        id: 2,
        nombre: 'Sin pedidos',
        direccion: 'Cll 2',
        necesidades_pendientes: 0,
      }),
    ]);

    renderRed();

    expect(await screen.findByText('3 necesidades activas')).toBeInTheDocument();
    expect(screen.queryByText(/0 necesidades/)).not.toBeInTheDocument();
  });

  it('sin resultados muestra el vacío con la invitación a registrar', async () => {
    renderRed();

    expect(await screen.findByText(/Aún no hay lugares registrados/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Registrar un lugar' })).toHaveAttribute(
      'href',
      '/ayudar/registrar',
    );
  });
});
