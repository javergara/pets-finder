import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import type { Reporte } from '../api/types';
import { ZONAS } from '../lib/ciudades';
import { setActiveUserId } from '../lib/session';
import { PuenteAdopcion } from './PuenteAdopcion';

// El puente reporte encontrado → adopción (AD-02, A3), lado frontend.
//
// El componente decide todo dentro y devuelve `null` en el caso común, así que
// lo que hay que fijar aquí es sobre todo cuándo NO aparece: el CTA escribe (y
// escribe en producción) y la franja informa a cualquiera que pase.

function crearReporte(overrides: Partial<Reporte> = {}): Reporte {
  return {
    id: 12,
    user_id: 7,
    tipo: 'encontrado',
    especie: 'gato',
    nombre_mascota: null,
    raza: null,
    color: 'carey',
    tamano: 'pequeño',
    descripcion: 'Gatita carey juvenil, la tengo en casa.',
    foto_url: '/media/seed/report_5.jpg',
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: 'La Castellana',
    lat: ZONAS.Armenia.centroLat,
    lng: ZONAS.Armenia.centroLng,
    situacion: 'conmigo',
    fecha_evento: '2026-08-11',
    telefono_contacto: '3001234561',
    instagram: null,
    facebook: null,
    fuente: 'manual',
    crawl_metadata: null,
    idempotency_id: null,
    estado: 'activo',
    creado_en: '2026-08-12T08:00:00',
    resuelto_en: null,
    ...overrides,
  };
}

function renderPuente(reporte: Reporte) {
  return render(
    <MemoryRouter>
      <PuenteAdopcion reporte={reporte} />
    </MemoryRouter>,
  );
}

describe('PuenteAdopcion — el CTA de darla en adopción', () => {
  it('el autor de un encontrado que tiene consigo ve el CTA con el reporte en la URL', () => {
    setActiveUserId(7);

    renderPuente(crearReporte());

    expect(screen.getByRole('link', { name: 'Darla en adopción' })).toHaveAttribute(
      'href',
      '/adoptar/publicar?reporte=12',
    );
  });

  it('quien no es el autor no ve el CTA', () => {
    setActiveUserId(9);

    const { container } = renderPuente(crearReporte());

    expect(container).toBeEmptyDOMElement();
  });

  it('un encontrado que solo fue visto no se puede dar en adopción', () => {
    setActiveUserId(7);

    const { container } = renderPuente(crearReporte({ situacion: 'vista' }));

    // No la tiene nadie: ofrecer darla en adopción sería prometer algo imposible
    // (y el backend responde 422).
    expect(container).toBeEmptyDOMElement();
  });

  it('un reporte de mascota perdida nunca ofrece el CTA, ni a su autor', () => {
    setActiveUserId(7);

    const { container } = renderPuente(crearReporte({ tipo: 'perdido', situacion: null }));

    expect(container).toBeEmptyDOMElement();
  });

  it('un reporte ya reunido no ofrece el CTA', () => {
    setActiveUserId(7);

    const { container } = renderPuente(crearReporte({ estado: 'reunido' }));

    expect(container).toBeEmptyDOMElement();
  });

  it('sin cuenta no hay CTA aunque el reporte sea del usuario demo', () => {
    // Sin `hasActiveUser()`, `getActiveUserId()` cae al DEMO_USER_ID (1) y
    // cualquier visitante vería el botón de escritura sobre los reportes del
    // usuario 1 en producción. Por eso el reporte de este caso es justo suyo.
    const { container } = renderPuente(crearReporte({ user_id: 1 }));

    expect(container).toBeEmptyDOMElement();
  });
});

describe('PuenteAdopcion — la franja de mascota ya publicada', () => {
  it('con adopcion_pet_id enlaza a la ficha, y la ve cualquiera (no solo el autor)', () => {
    setActiveUserId(99);

    renderPuente(crearReporte({ adopcion_pet_id: 55 }));

    // La franja es información pública: quien llega por un link compartido tiene
    // que poder seguir el rastro hasta la ficha de adopción.
    expect(screen.getByText(/Ahora en adopción/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ver su ficha de adopción' })).toHaveAttribute(
      'href',
      '/adoptar/mascota/55',
    );
    expect(screen.queryByRole('link', { name: 'Darla en adopción' })).not.toBeInTheDocument();
  });
});
