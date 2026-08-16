import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from './api/client';
import App from './App';
import { setActiveUserId } from './lib/session';

// La landing pide el resumen de reencuentros al montar; el deck de AD-03 pide su
// baraja. Se mockean las dos para que ninguna ruta salga a la red de verdad.
vi.mock('./api/client', async () => {
  const actual = await vi.importActual<typeof client>('./api/client');
  return {
    ...actual,
    obtenerReunidos: vi.fn(),
    listarDeck: vi.fn(),
    obtenerPerfilHogar: vi.fn(),
  };
});

beforeEach(() => {
  vi.mocked(client.obtenerReunidos).mockResolvedValue({ total: 0, recientes: [] });
  vi.mocked(client.listarDeck).mockResolvedValue([]);
  vi.mocked(client.obtenerPerfilHogar).mockResolvedValue(null);
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
});
