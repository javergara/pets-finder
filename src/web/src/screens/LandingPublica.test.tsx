import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { LandingPublica } from './LandingPublica';

// La landing no llama a la API (contenido 100% estático): a diferencia de
// Descubrir.test.tsx/Favoritos.test.tsx, no hay ningún mock de `../api/client` aquí.

function renderConRouter() {
  return render(
    <MemoryRouter>
      <LandingPublica />
    </MemoryRouter>,
  );
}

describe('LandingPublica', () => {
  it('muestra el headline exacto del hero', () => {
    renderConRouter();

    expect(screen.getByText('Adoptar bien empieza por conocerse bien.')).toBeInTheDocument();
  });

  it('muestra las 3 cifras de credibilidad', () => {
    renderConRouter();

    expect(screen.getByText('2.140')).toBeInTheDocument();
    expect(screen.getByText('adopciones cerradas')).toBeInTheDocument();
    expect(screen.getByText('86')).toBeInTheDocument();
    expect(screen.getByText('refugios verificados')).toBeInTheDocument();
    expect(screen.getByText('7%')).toBeInTheDocument();
    expect(screen.getByText('tasa de devolución')).toBeInTheDocument();
  });

  it('muestra los 4 pasos de "Cómo funciona" con su título', () => {
    renderConRouter();

    expect(screen.getByRole('heading', { level: 2, name: 'Cómo funciona' })).toBeInTheDocument();
    expect(screen.getByText('Cuéntanos de tu hogar')).toBeInTheDocument();
    expect(screen.getByText('Desliza con criterio')).toBeInTheDocument();
    expect(screen.getByText('Habla con el refugio')).toBeInTheDocument();
    expect(screen.getByText('Conócense en persona')).toBeInTheDocument();
  });

  it('muestra el grid 2x2 de "por qué el cuestionario"', () => {
    renderConRouter();

    expect(screen.getByText('6')).toBeInTheDocument();
    expect(screen.getByText('preguntas antes de ver el primer perfil')).toBeInTheDocument();
    expect(screen.getByText('24 h')).toBeInTheDocument();
    expect(screen.getByText('tiempo medio de respuesta del refugio')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('visita presencial obligatoria antes de entregar')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('costo para adoptantes y refugios')).toBeInTheDocument();
  });

  it('los CTAs navegan a los destinos correctos', () => {
    renderConRouter();

    expect(screen.getByRole('link', { name: /empezar el cuestionario/i })).toHaveAttribute(
      'href',
      '/cuestionario',
    );
    expect(screen.getByRole('link', { name: /soy un refugio/i })).toHaveAttribute(
      'href',
      '/refugio',
    );
    expect(screen.getByRole('link', { name: /entrar a la app/i })).toHaveAttribute(
      'href',
      '/descubrir',
    );
    expect(screen.getByRole('link', { name: /ver quién necesita apoyo/i })).toHaveAttribute(
      'href',
      '/apadrinar',
    );
    expect(screen.getByRole('link', { name: /registrar mi refugio/i })).toHaveAttribute(
      'href',
      '/refugio',
    );
  });

  it('las anclas del nav apuntan a las secciones correspondientes', () => {
    renderConRouter();

    const enlacesComo = screen.getAllByRole('link', { name: 'Cómo funciona' });
    expect(enlacesComo.length).toBeGreaterThan(0);
    enlacesComo.forEach((enlace) => expect(enlace).toHaveAttribute('href', '#como'));

    const enlacesApadrinar = screen.getAllByRole('link', { name: 'Apadrinar' });
    expect(enlacesApadrinar.length).toBeGreaterThan(0);
    enlacesApadrinar.forEach((enlace) => expect(enlace).toHaveAttribute('href', '#apadrinar'));

    expect(screen.getByRole('link', { name: 'Para refugios' })).toHaveAttribute(
      'href',
      '#refugios',
    );
    expect(screen.getByRole('link', { name: 'Refugios' })).toHaveAttribute('href', '#refugios');
  });

  it('muestra Canela y Toribio en la franja de apadrinamiento', () => {
    renderConRouter();

    // "Canela" aparece dos veces (tarjeta de apadrinamiento y fila de la tabla mock de
    // refugios), así que se verifica presencia con getAllByText en vez de getByText.
    expect(screen.getAllByText('Canela').length).toBeGreaterThan(0);
    expect(screen.getByText('Tratamiento de cadera')).toBeInTheDocument();
    expect(screen.getByText('Toribio')).toBeInTheDocument();
    expect(screen.getByText('Vacunas y esterilización')).toBeInTheDocument();
  });

  it('muestra la tabla mock con encabezados y al menos una fila de ejemplo', () => {
    renderConRouter();

    expect(screen.getByText('Adoptante')).toBeInTheDocument();
    expect(screen.getByText('Mascota')).toBeInTheDocument();
    expect(screen.getByText('Afinidad')).toBeInTheDocument();
    expect(screen.getByText('Valentina Ríos')).toBeInTheDocument();
    const filaLuna = screen.getAllByText('Luna')[0];
    expect(filaLuna).toBeInTheDocument();
    expect(screen.getByText('94%')).toBeInTheDocument();
  });

  it('el footer repite las anclas y el nombre de la marca', () => {
    renderConRouter();

    expect(screen.getByText('Adopta · Colombia · 2026')).toBeInTheDocument();
    const footer = screen.getByText('Adopta · Colombia · 2026').closest('footer');
    expect(footer).not.toBeNull();
    expect(
      within(footer as HTMLElement).getByRole('link', { name: 'Privacidad' }),
    ).toBeInTheDocument();
  });
});
