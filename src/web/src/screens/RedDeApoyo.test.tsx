import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Organizacion } from '../api/types';
import { setActiveUserId } from '../lib/session';
import { RedDeApoyo } from './RedDeApoyo';

// Fix 2026-08-15 (bug de autoría sin cuenta): el caso del autor declara su cuenta
// con `setActiveUserId(1)`. Antes no la declaraba y pasaba igual, porque sin nada
// en localStorage `getActiveUserId()` cae al usuario demo (id 1) y la pantalla lo
// daba por autor del aviso — fijaba el bug.

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    listarOrganizaciones: vi.fn(),
    listarAvisosAyuda: vi.fn(),
    resolverAvisoAyuda: vi.fn(),
    eliminarAvisoAyuda: vi.fn(),
  };
});

beforeEach(() => {
  vi.mocked(client.listarAvisosAyuda).mockResolvedValue([]);
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

function crearAviso(overrides: Partial<import('../api/types').AvisoAyuda> = {}) {
  return {
    id: 1,
    user_id: 7,
    tipo: 'ofrezco' as const,
    categoria: 'hogar_de_paso' as const,
    titulo: 'Ofrezco mi casa como hogar de paso',
    descripcion: 'Tengo espacio y experiencia.',
    zona: 'Cali',
    ciudad_texto: null,
    barrio: 'Los Chorros',
    telefono_contacto: '3001234567',
    estado: 'activo' as const,
    creado_en: new Date(Date.now() - 3_600_000).toISOString(),
    resuelto_en: null,
    ...overrides,
  };
}

describe('RedDeApoyo — Comunidad (feature 42)', () => {
  it('la pestaña Comunidad lista los avisos con tipo, categoría y WhatsApp correcto', async () => {
    vi.mocked(client.listarOrganizaciones).mockResolvedValue([]);
    vi.mocked(client.listarAvisosAyuda).mockResolvedValue([crearAviso()]);

    renderRed();
    fireEvent.click(screen.getByRole('button', { name: 'Comunidad' }));

    expect(await screen.findByText('Ofrezco mi casa como hogar de paso')).toBeInTheDocument();
    // 'Ofrece ayuda' existe como chip de filtro y como badge de la tarjeta.
    expect(screen.getAllByText('Ofrece ayuda')).toHaveLength(2);
    // 'Hogar de paso' existe también como opción del select de categorías.
    expect(screen.getAllByText('Hogar de paso').length).toBeGreaterThan(1);
    const whatsapp = screen.getByRole('link', { name: 'WhatsApp' });
    expect(whatsapp.getAttribute('href')).toBe(
      `https://wa.me/573001234567?text=${encodeURIComponent(
        'Hola, vi tu aviso en Pet Finder Col: "Ofrezco mi casa como hogar de paso".',
      )}`,
    );
    // Aviso de seguridad de la feature 40 presente en la Comunidad.
    expect(screen.getByText(/nadie debe pedirte dinero/)).toBeInTheDocument();
  });

  it('el autor puede marcar resuelto; otros no ven los controles', async () => {
    setActiveUserId(1);
    vi.mocked(client.listarOrganizaciones).mockResolvedValue([]);
    vi.mocked(client.listarAvisosAyuda).mockResolvedValue([
      crearAviso({ id: 2, user_id: 1, titulo: 'Mi propio aviso' }),
      crearAviso({ id: 3, user_id: 99, titulo: 'Aviso ajeno' }),
    ]);
    vi.mocked(client.resolverAvisoAyuda).mockResolvedValue(
      crearAviso({ id: 2, user_id: 1, estado: 'resuelto' }),
    );

    renderRed();
    fireEvent.click(screen.getByRole('button', { name: 'Comunidad' }));
    await screen.findByText('Mi propio aviso');

    // Solo un aviso (el propio) tiene el botón de resolver.
    const botones = screen.getAllByRole('button', { name: 'Marcar resuelto 💚' });
    expect(botones).toHaveLength(1);

    fireEvent.click(botones[0]);
    expect(await screen.findByText('Resuelto 💚')).toBeInTheDocument();
    expect(client.resolverAvisoAyuda).toHaveBeenCalledWith(2, 1);
  });

  // Fix 2026-08-15 (bug de autoría sin cuenta): sin nadie registrado, el aviso del
  // usuario demo (id 1) no tiene autor presente, así que no se puede resolver ni
  // eliminar. Leer los avisos y escribir por WhatsApp sí sigue siendo público.
  it('sin cuenta, el aviso del usuario demo no ofrece resolver ni eliminar', async () => {
    vi.mocked(client.listarOrganizaciones).mockResolvedValue([]);
    vi.mocked(client.listarAvisosAyuda).mockResolvedValue([
      crearAviso({ id: 2, user_id: 1, titulo: 'Aviso del usuario demo' }),
    ]);

    renderRed();
    fireEvent.click(screen.getByRole('button', { name: 'Comunidad' }));

    expect(await screen.findByText('Aviso del usuario demo')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'WhatsApp' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Marcar resuelto 💚' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Eliminar' })).not.toBeInTheDocument();
  });

  it('los botones de publicar llevan a /ayudar/publicar-aviso con el tipo', async () => {
    vi.mocked(client.listarOrganizaciones).mockResolvedValue([]);
    vi.mocked(client.listarAvisosAyuda).mockResolvedValue([]);

    renderRed();
    fireEvent.click(screen.getByRole('button', { name: 'Comunidad' }));

    expect(await screen.findByRole('link', { name: 'Necesito ayuda' })).toHaveAttribute(
      'href',
      '/ayudar/publicar-aviso?tipo=pido',
    );
    expect(screen.getByRole('link', { name: 'Quiero ayudar' })).toHaveAttribute(
      'href',
      '/ayudar/publicar-aviso?tipo=ofrezco',
    );
  });
});

describe('RedDeApoyo', () => {
  it('se titula Centros de ayuda (feature 35: la pestaña dice lo que hace)', async () => {
    vi.mocked(client.listarOrganizaciones).mockResolvedValue([]);

    renderRed();

    expect(await screen.findByRole('heading', { name: 'Centros de ayuda' })).toBeInTheDocument();
  });

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

  it('el chip Entrenador filtra y su tarjeta muestra la etiqueta (feature 47)', async () => {
    vi.mocked(client.listarOrganizaciones).mockResolvedValue([
      crearOrganizacion({
        id: 9,
        tipo: 'entrenador',
        nombre: 'Camilo Adiestramiento Canino',
        como_donar: 'Primera valoración gratuita',
      }),
    ]);

    renderRed();
    // El chip existe (filtro y leyenda a la vez) y re-consulta con el tipo.
    fireEvent.click(await screen.findByRole('button', { name: /Entrenador/ }));
    await waitFor(() =>
      expect(client.listarOrganizaciones).toHaveBeenLastCalledWith({
        tipo: 'entrenador',
        zona: undefined,
      }),
    );
    expect((await screen.findAllByText('Entrenador')).length).toBeGreaterThan(1);
    expect(screen.getByText('Camilo Adiestramiento Canino')).toBeInTheDocument();
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
