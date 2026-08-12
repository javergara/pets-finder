import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { LandingEmergencia } from './LandingEmergencia';

function renderLanding() {
  return render(
    <MemoryRouter>
      <LandingEmergencia />
    </MemoryRouter>,
  );
}

describe('LandingEmergencia', () => {
  it('muestra los dos CTAs gigantes con sus destinos', () => {
    renderLanding();

    expect(screen.getByRole('link', { name: 'Perdí a mi mascota' })).toHaveAttribute(
      'href',
      '/reportar/perdido',
    );
    expect(screen.getByRole('link', { name: 'Encontré una mascota' })).toHaveAttribute(
      'href',
      '/reportar/encontrado',
    );
  });

  it('da acceso al listado y al mapa', () => {
    renderLanding();

    expect(screen.getByRole('link', { name: 'Ver todos los reportes' })).toHaveAttribute(
      'href',
      '/reportes',
    );
    expect(screen.getByRole('link', { name: 'Ver el mapa' })).toHaveAttribute('href', '/mapa');
  });

  it('nombra las zonas cubiertas incluyendo Cali y Quibdó', () => {
    renderLanding();

    expect(
      screen.getByText(/Armenia · Pereira · Manizales · Cali · Quibdó · Bogotá/),
    ).toBeInTheDocument();
  });
});
