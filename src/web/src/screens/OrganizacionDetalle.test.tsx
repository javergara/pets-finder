import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Organizacion } from '../api/types';
import { setActiveUserId } from '../lib/session';
import { OrganizacionDetalle } from './OrganizacionDetalle';

// Fix 2026-08-15 (bug de autoría sin cuenta): los casos que ejercitan al autor
// declaran su cuenta con `setActiveUserId(1)`. Antes no la declaraban y pasaban
// igual, porque sin nada en localStorage `getActiveUserId()` cae al usuario demo
// (id 1) y la pantalla lo daba por autor — es decir, fijaban el bug.

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    obtenerOrganizacion: vi.fn(),
    editarOrganizacion: vi.fn(),
    eliminarOrganizacion: vi.fn(),
    listarNecesidades: vi.fn(),
    listarMascotas: vi.fn(),
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

// AD-02: la pestaña de adopción se puede abrir desde la URL para volver aquí
// después de publicar una mascota (`/organizacion/1?tab=adopcion`).
function renderDetalleEnAdopcion() {
  return render(
    <MemoryRouter initialEntries={['/organizacion/1?tab=adopcion']}>
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
    // La cuenta activa es la 1 y el lugar es de la 2: alguien con cuenta que
    // mira un lugar ajeno (el caso sin cuenta tiene su propio describe abajo).
    setActiveUserId(1);
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion({ user_id: 2 }));

    renderDetalle();

    await screen.findByRole('heading', { name: 'Fundación Huellitas' });
    expect(screen.queryByText('Administrar')).not.toBeInTheDocument();
  });

  it('el autor edita horario y cómo donar, y el guardado llama al API', async () => {
    setActiveUserId(1);
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
    setActiveUserId(1);
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
    setActiveUserId(1);
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
    setActiveUserId(1);
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion({ user_id: 1 }));
    vi.mocked(client.eliminarOrganizacion).mockResolvedValue(undefined);

    renderDetalle();

    (await screen.findByRole('button', { name: 'Eliminar este lugar' })).click();
    expect(client.eliminarOrganizacion).not.toHaveBeenCalled();
    (await screen.findByRole('button', { name: 'Sí, eliminar' })).click();

    await screen.findByText('Red stub');
    expect(client.eliminarOrganizacion).toHaveBeenCalledWith(1, 1);
  });

  // Fix 2026-08-15: mismo bug que en ReporteDetalle — la carga iba sin `.catch`
  // y una organización inexistente (o eliminada) dejaba el esqueleto para siempre.
  it('si la organización no existe muestra el mensaje del backend y la salida a /ayudar, sin esqueleto', async () => {
    vi.mocked(client.obtenerOrganizacion).mockRejectedValue(
      new client.ApiError('La organización 999 no existe'),
    );
    vi.mocked(client.listarNecesidades).mockRejectedValue(
      new client.ApiError('La organización 999 no existe'),
    );

    renderDetalle();

    expect(await screen.findByRole('alert')).toHaveTextContent('La organización 999 no existe');
    expect(screen.getByRole('link', { name: /Ver los centros de ayuda/i })).toHaveAttribute(
      'href',
      '/ayudar',
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  // AD-02 (A1): el lugar gana una segunda pestaña con las mascotas que da en
  // adopción. La ficha de siempre sigue siendo la pestaña por defecto.
  it('la pestaña "En adopción" existe y al abrirla monta el panel', async () => {
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion());
    vi.mocked(client.listarMascotas).mockResolvedValue([]);

    renderDetalle();

    await screen.findByRole('heading', { name: 'Fundación Huellitas' });
    expect(screen.getByText('Qué hacen')).toBeInTheDocument();
    // Sin abrir la pestaña, el panel ni siquiera pide las mascotas.
    expect(client.listarMascotas).not.toHaveBeenCalled();

    screen.getByRole('button', { name: 'En adopción' }).click();

    expect(await screen.findByText(/todavía no tiene mascotas publicadas/i)).toBeInTheDocument();
    expect(screen.queryByText('Qué hacen')).not.toBeInTheDocument();
  });

  it('con ?tab=adopcion la pestaña de adopción abre montada', async () => {
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion());
    vi.mocked(client.listarMascotas).mockResolvedValue([]);

    renderDetalleEnAdopcion();

    // Es adonde vuelve quien acaba de publicar una mascota desde este lugar.
    expect(await screen.findByText(/todavía no tiene mascotas publicadas/i)).toBeInTheDocument();
    expect(client.listarMascotas).toHaveBeenCalledWith({ organizacionId: 1, estado: 'todos' });
    expect(screen.queryByText('Qué hacen')).not.toBeInTheDocument();
    // El encabezado del lugar no depende de la pestaña.
    expect(screen.getByRole('heading', { name: 'Fundación Huellitas' })).toBeInTheDocument();
  });

  it('un fallo de red también sale del esqueleto, con copy en español', async () => {
    vi.mocked(client.obtenerOrganizacion).mockRejectedValue(new Error('offline'));

    renderDetalle();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No pudimos cargar este lugar. Revisa tu conexión e intenta de nuevo.',
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});

// Fix 2026-08-15 (bug de autoría sin cuenta). Reproducido en navegador real en
// /organizacion/1 con el localStorage vacío: la pantalla mostraba "Editar
// información" y "Eliminar este lugar" de una organización de una persona real.
// Sin cuenta no hay autoría posible, y el user_id 1 es justo el que lo delata.
describe('OrganizacionDetalle sin cuenta', () => {
  it('no ofrece ningún control de escritura sobre el lugar del usuario demo', async () => {
    vi.mocked(client.obtenerOrganizacion).mockResolvedValue(crearOrganizacion({ user_id: 1 }));

    renderDetalle();

    // La ficha pública se ve entera: mirar nunca pide cuenta.
    expect(await screen.findByRole('heading', { name: 'Fundación Huellitas' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Escribir por WhatsApp' })).toBeInTheDocument();

    expect(screen.queryByText('Administrar')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Editar información' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Eliminar este lugar' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Marcar como cerrado' })).not.toBeInTheDocument();
    // Las necesidades tampoco: publicar y marcar cubierta son del autor.
    expect(screen.queryByLabelText('¿Qué necesitan?')).not.toBeInTheDocument();
  });
});
