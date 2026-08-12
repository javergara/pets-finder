import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import App from './App';

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
