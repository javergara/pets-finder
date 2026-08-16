import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from './api/client';
import App from './App';
import { setActiveUserId } from './lib/session';

// La landing pide el resumen de reencuentros al montar; el deck de AD-03 pide su
// baraja, "Mis solicitudes" (AD-05) sus dos listas y el catálogo (AD-01) su
// listado más el resumen de adopciones. Se mockean todas para que ninguna ruta
// salga a la red de verdad.
vi.mock('./api/client', async () => {
  const actual = await vi.importActual<typeof client>('./api/client');
  return {
    ...actual,
    obtenerReunidos: vi.fn(),
    listarDeck: vi.fn(),
    obtenerPerfilHogar: vi.fn(),
    listarSolicitudes: vi.fn(),
    obtenerSolicitud: vi.fn(),
    listarMascotas: vi.fn(),
    obtenerAdopcionesResumen: vi.fn(),
  };
});

beforeEach(() => {
  vi.mocked(client.obtenerReunidos).mockResolvedValue({ total: 0, recientes: [] });
  vi.mocked(client.listarDeck).mockResolvedValue([]);
  vi.mocked(client.obtenerPerfilHogar).mockResolvedValue(null);
  vi.mocked(client.listarSolicitudes).mockResolvedValue([]);
  vi.mocked(client.listarMascotas).mockResolvedValue([]);
  vi.mocked(client.obtenerAdopcionesResumen).mockResolvedValue({ total: 0, recientes: [] });
  // El detalle se queda en su esqueleto: lo que este archivo comprueba es que la
  // ruta monta la pantalla dentro de AppLayout, no lo que la pantalla pinta
  // después (eso vive en `SolicitudDetalle.test.tsx`).
  vi.mocked(client.obtenerSolicitud).mockReturnValue(new Promise(() => {}));
  setActiveUserId(1);
});

// `App` no envuelve un `BrowserRouter` internamente (eso vive en `main.tsx`), así que
// puede montarse directamente dentro de un `MemoryRouter` de test, igual que cada
// pantalla individual.

describe('App', () => {
  it('en "/" renderiza la landing de emergencia sin el <Nav/> interno', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole('link', { name: 'Perdí a mi mascota' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Encontré una mascota' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Mis reportes' })).not.toBeInTheDocument();
  });

  it('en "/registro" el <Nav/> interno sí se renderiza con la marca Pet Finder Col', () => {
    render(
      <MemoryRouter initialEntries={['/registro']}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole('link', { name: 'Pet Finder Col' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Mis reportes' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Entra o crea tu cuenta' })).toBeInTheDocument();
  });

  // Desde AD-08 el catálogo sí se anuncia en la nav, así que su ruta merece el
  // mismo caso de montaje que las otras cuatro del módulo.
  it('en "/adoptar" monta el catálogo con el <Nav/> interno', async () => {
    render(
      <MemoryRouter initialEntries={['/adoptar']}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole('heading', { name: 'Mascotas en adopción' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Pet Finder Col' })).toBeInTheDocument();
  });

  // La ruta del deck (AD-03) existe y es compartible aunque todavía no se anuncie
  // en la nav: va DENTRO de AppLayout, como el resto del módulo de adopción.
  it('en "/adoptar/descubrir" monta el deck con el <Nav/> interno', async () => {
    render(
      <MemoryRouter initialEntries={['/adoptar/descubrir']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: 'Descubrir' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Pet Finder Col' })).toBeInTheDocument();
  });

  // El cuestionario de hogar (AD-04) vive dentro de AppLayout como el resto del
  // módulo. Con cuenta activa se monta el wizard; sin ella se iría al registro,
  // que es el caso propio de `CuestionarioHogar.test.tsx`.
  it('en "/adoptar/mi-hogar" monta el cuestionario de hogar', async () => {
    render(
      <MemoryRouter initialEntries={['/adoptar/mi-hogar']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText('Paso 1 de 6')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Pet Finder Col' })).toBeInTheDocument();
  });

  // "Mis solicitudes" (AD-05) vive dentro de AppLayout como el resto del módulo.
  // Con cuenta activa se monta la pantalla; sin ella se iría al registro, que es
  // el caso propio de `MisSolicitudes.test.tsx`.
  it('en "/adoptar/mis-solicitudes" monta las solicitudes con el <Nav/> interno', async () => {
    render(
      <MemoryRouter initialEntries={['/adoptar/mis-solicitudes']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: 'Mis solicitudes' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Pet Finder Col' })).toBeInTheDocument();
  });

  // El detalle de una solicitud (AD-05, paso 7) es una ruta dinámica y va
  // también dentro de AppLayout: se llega desde cualquiera de las dos listas.
  it('en "/adoptar/solicitud/:id" monta el detalle con el <Nav/> interno', async () => {
    render(
      <MemoryRouter initialEntries={['/adoptar/solicitud/42']}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole('status', { name: /cargando la solicitud/i }),
    ).toBeInTheDocument();
    expect(client.obtenerSolicitud).toHaveBeenCalledWith(42, 1);
    expect(screen.getByRole('link', { name: 'Pet Finder Col' })).toBeInTheDocument();
  });

  it('la marca de la nav es el logo oficial y la pestaña de ayuda dice Centros de ayuda (feature 35)', () => {
    render(
      <MemoryRouter initialEntries={['/registro']}>
        <App />
      </MemoryRouter>,
    );

    const logo = screen.getByAltText('Pet Finder Col');
    expect(logo).toHaveAttribute('src', '/logo.svg');
    expect(logo.closest('a')).toHaveAttribute('href', '/');
    expect(screen.getByRole('link', { name: 'Centros de ayuda' })).toHaveAttribute(
      'href',
      '/ayudar',
    );
  });

  // ⚠️ LA SECUENCIA COMPLETA, no "existe un enlace a /adoptar". El orden de la
  // nav es la jerarquía del producto: emergencia primero (reportar, buscar,
  // mirar el mapa, lo mío) y la adopción después, como fase 2. Aseverar la lista
  // entera es lo único que detecta que "Adoptar" se cuele delante de "Reportes"
  // —o que alguien mueva de sitio cualquiera de los otros seis— y evita índices
  // mágicos: el caso se lee como la nav que se ve en pantalla.
  it('la nav lista los ocho enlaces en su orden exacto, con Adoptar detrás de la emergencia (AD-08)', () => {
    render(
      <MemoryRouter initialEntries={['/registro']}>
        <App />
      </MemoryRouter>,
    );

    // El primero es el logo: su texto accesible vive en el `alt` de la imagen.
    const etiqueta = (enlace: HTMLElement) =>
      `${enlace.getAttribute('href')} ${
        enlace.textContent || enlace.querySelector('img')?.getAttribute('alt') || ''
      }`;

    const enlaces = within(screen.getByRole('navigation')).getAllByRole('link');

    expect(enlaces.map(etiqueta)).toEqual([
      '/ Pet Finder Col',
      '/reportar/perdido Perdí mi mascota',
      '/reportar/encontrado Encontré una mascota',
      '/reportes Reportes',
      '/mapa Mapa',
      '/mis-reportes Mis reportes',
      '/adoptar Adoptar',
      '/ayudar Centros de ayuda',
    ]);
  });
});
