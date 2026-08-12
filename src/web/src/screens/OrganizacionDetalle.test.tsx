import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Organizacion } from '../api/types';
import { OrganizacionDetalle } from './OrganizacionDetalle';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    obtenerOrganizacion: vi.fn(),
    editarOrganizacion: vi.fn(),
    eliminarOrganizacion: vi.fn(),
    listarNecesidades: vi.fn(),
    crearNecesidad: vi.fn(),
    cubrirNecesidad: vi.fn(),
  };
});

beforeEach(() => {
  vi.mocked(client.listarNecesidades).mockResolvedValue([]);
});

afterEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
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

function renderDetalle() {
  return render(
    <MemoryRouter initialEntries={['/organizacion/1']}>
      <Routes>
        <Route path="/organizacion/:id" element={<OrganizacionDetalle />} />
        <Route path="/ayudar" element={<div>Red stub</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('OrganizacionDetalle', () => {
  it('muestra la información completa y los hrefs exactos de contacto', async () => {
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion());

    renderDetalle();

    expect(await screen.findByRole('heading', { name: 'Fundación Huellitas' })).toBeInTheDocument();
    expect(screen.getByText('Rescatamos mascotas afectadas por el sismo.')).toBeInTheDocument();
    expect(screen.getByText(/Cra 14 #10-25/)).toBeInTheDocument();
    expect(screen.getByText('Horario: Lun-Sáb 8am-5pm')).toBeInTheDocument();
    expect(screen.getByText('Nequi 3001112233')).toBeInTheDocument();

    const whatsapp = screen.getByRole('link', { name: 'Escribir por WhatsApp' });
    const href = whatsapp.getAttribute('href') ?? '';
    expect(href.startsWith('https://wa.me/573001112233?text=')).toBe(true);
    const texto = decodeURIComponent(href.split('?text=')[1]);
    expect(texto).toContain('Pet Finder Col');
    expect(texto).toContain('Fundación Huellitas');
    expect(screen.getByRole('link', { name: 'Llamar' })).toHaveAttribute(
      'href',
      'tel:+573001112233',
    );
  });

  it('sin como_donar no muestra la sección Cómo donar', async () => {
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(
      crearOrganizacion({ como_donar: null }),
    );

    renderDetalle();

    await screen.findByRole('heading', { name: 'Fundación Huellitas' });
    expect(screen.queryByText('Cómo donar')).not.toBeInTheDocument();
  });

  it('el bloque Administrar solo aparece para el autor', async () => {
    // getActiveUserId() cae a DEMO_USER_ID=1; la org es de user_id 2.
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion({ user_id: 2 }));

    renderDetalle();

    await screen.findByRole('heading', { name: 'Fundación Huellitas' });
    expect(screen.queryByText('Administrar')).not.toBeInTheDocument();
  });

  it('el autor edita horario y cómo donar, y el guardado llama al API', async () => {
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion({ user_id: 1 }));
    vi.mocked(client.editarOrganizacion).mockResolvedValue(
      crearOrganizacion({ horario: 'Lun-Dom 24h' }),
    );

    renderDetalle();

    (await screen.findByRole('button', { name: 'Editar información' })).click();
    fireEvent.change(await screen.findByLabelText('Horario'), {
      target: { value: 'Lun-Dom 24h' },
    });
    screen.getByRole('button', { name: 'Guardar cambios' }).click();

    expect(await screen.findByText('Horario: Lun-Dom 24h')).toBeInTheDocument();
    expect(client.editarOrganizacion).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ user_id: 1, horario: 'Lun-Dom 24h' }),
    );
  });

  it('cerrar el lugar muestra el aviso y oculta el contacto', async () => {
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion({ user_id: 1 }));
    vi.mocked(client.editarOrganizacion).mockResolvedValue(
      crearOrganizacion({ user_id: 1, estado: 'cerrado' }),
    );

    renderDetalle();

    (await screen.findByRole('button', { name: 'Marcar como cerrado' })).click();

    expect(await screen.findByText('Este lugar está marcado como cerrado.')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Escribir por WhatsApp' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reabrir' })).toBeInTheDocument();
  });

  it('las necesidades pendientes tienen "Quiero ayudar" con el prefill exacto y las cubiertas celebran', async () => {
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion({ user_id: 2 }));
    vi.mocked(client.listarNecesidades).mockResolvedValue([
      {
        id: 1,
        organizacion_id: 1,
        categoria: 'alimento',
        descripcion: '50 kg de comida para perro adulto',
        estado: 'pendiente',
        creado_en: '2026-08-12T10:00:00',
        cubierta_en: null,
      },
      {
        id: 2,
        organizacion_id: 1,
        categoria: 'voluntarios',
        descripcion: 'Brigada del sábado',
        estado: 'cubierta',
        creado_en: '2026-08-11T10:00:00',
        cubierta_en: '2026-08-12T09:00:00',
      },
    ]);

    renderDetalle();

    expect(await screen.findByText(/50 kg de comida/)).toBeInTheDocument();
    const ayudar = screen.getByRole('link', { name: 'Quiero ayudar' });
    const href = ayudar.getAttribute('href') ?? '';
    expect(href.startsWith('https://wa.me/573001112233?text=')).toBe(true);
    expect(decodeURIComponent(href.split('?text=')[1])).toBe(
      'Hola, vi en Pet Finder Col que necesitan 50 kg de comida para perro adulto. Quiero ayudar.',
    );
    expect(screen.getByText('Cubierta 💚')).toBeInTheDocument();
    // No-autor: sin form de publicar ni marcar cubierta.
    expect(screen.queryByLabelText('¿Qué necesitan?')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Marcar cubierta' })).not.toBeInTheDocument();
  });

  it('el autor publica una necesidad y la marca cubierta', async () => {
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion({ user_id: 1 }));
    const pendiente = {
      id: 5,
      organizacion_id: 1,
      categoria: 'medicinas' as const,
      descripcion: 'Antipulgas para cachorros',
      estado: 'pendiente' as const,
      creado_en: '2026-08-12T11:00:00',
      cubierta_en: null,
    };
    vi.mocked(client.crearNecesidad).mockResolvedValue(pendiente);
    vi.mocked(client.cubrirNecesidad).mockResolvedValue({
      ...pendiente,
      estado: 'cubierta',
      cubierta_en: '2026-08-12T12:00:00',
    });

    renderDetalle();

    fireEvent.change(await screen.findByLabelText('Categoría'), {
      target: { value: 'medicinas' },
    });
    fireEvent.change(screen.getByLabelText('¿Qué necesitan?'), {
      target: { value: 'Antipulgas para cachorros' },
    });
    screen.getByRole('button', { name: 'Publicar' }).click();

    expect(await screen.findByText(/Antipulgas para cachorros/)).toBeInTheDocument();
    expect(client.crearNecesidad).toHaveBeenCalledWith(1, {
      user_id: 1,
      categoria: 'medicinas',
      descripcion: 'Antipulgas para cachorros',
    });

    (await screen.findByRole('button', { name: 'Marcar cubierta' })).click();
    expect(await screen.findByText('Cubierta 💚')).toBeInTheDocument();
    expect(client.cubrirNecesidad).toHaveBeenCalledWith(1, 5, 1);
  });

  it('eliminar exige confirmación y navega a la red de apoyo', async () => {
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion({ user_id: 1 }));
    vi.mocked(client.eliminarOrganizacion).mockResolvedValue(undefined);

    renderDetalle();

    (await screen.findByRole('button', { name: 'Eliminar este lugar' })).click();
    expect(client.eliminarOrganizacion).not.toHaveBeenCalled();
    (await screen.findByRole('button', { name: 'Sí, eliminar' })).click();

    await screen.findByText('Red stub');
    expect(client.eliminarOrganizacion).toHaveBeenCalledWith(1, 1);
  });
});
