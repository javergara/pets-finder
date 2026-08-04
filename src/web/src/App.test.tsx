import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as client from './api/client';
import App from './App';

// `App` no envuelve un `BrowserRouter` internamente (eso vive en `main.tsx`), así que
// puede montarse directamente dentro de un `MemoryRouter` de test, igual que cada
// pantalla individual.

// `/descubrir` monta `Descubrir.tsx`, que llama a `api/client` al montar — mismo patrón
// de mock que `Descubrir.test.tsx`.
vi.mock('./api/client', async () => {
  const actual = await vi.importActual<typeof client>('./api/client');
  return {
    ...actual,
    listarMascotas: vi.fn(),
    registrarSwipe: vi.fn(),
    marcarFavorito: vi.fn(),
    desmarcarFavorito: vi.fn(),
  };
});

afterEach(() => {
  vi.resetAllMocks();
});

describe('App', () => {
  it('en "/" renderiza la landing pública sin el <Nav/> interno', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByText('Adoptar bien empieza por conocerse bien.')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Descubrir' })).not.toBeInTheDocument();
  });

  it('en "/descubrir" el <Nav/> interno sí se renderiza', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([]);

    render(
      <MemoryRouter initialEntries={['/descubrir']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('link', { name: 'Descubrir' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Favoritos' })).toBeInTheDocument();
    expect(screen.queryByText('Adoptar bien empieza por conocerse bien.')).not.toBeInTheDocument();
  });
});
