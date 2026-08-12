import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from './api/client';
import App from './App';

// La landing pide el resumen de reencuentros al montar.
vi.mock('./api/client', async () => {
  const actual = await vi.importActual<typeof client>('./api/client');
  return { ...actual, obtenerReunidos: vi.fn() };
});

beforeEach(() => {
  vi.mocked(client.obtenerReunidos).mockResolvedValue({ total: 0, recientes: [] });
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

  it('en "/registro" el <Nav/> interno sí se renderiza con la marca Reencuentro', () => {
    render(
      <MemoryRouter initialEntries={['/registro']}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole('link', { name: 'Reencuentro' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Mis reportes' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Crea tu cuenta' })).toBeInTheDocument();
  });
});
