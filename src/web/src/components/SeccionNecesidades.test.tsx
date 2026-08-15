import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Necesidad, Organizacion } from '../api/types';
import { SeccionNecesidades } from './SeccionNecesidades';

// Extraída de `OrganizacionDetalle` (AD-02 paso 4). El comportamiento completo
// (publicar, marcar cubierta, "Quiero ayudar") lo cubre `OrganizacionDetalle.test.tsx`,
// que es la red de seguridad del refactor y no se tocó. Aquí solo se fija la regla
// de visibilidad, que en la pantalla vivía como condición del JSX y ahora es del
// componente: sin necesidades y sin ser el autor, no hay sección que mostrar.

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
    horario: null,
    como_donar: null,
    foto_url: null,
    estado: 'activo',
    creado_en: '2026-08-12T10:00:00',
    necesidades_pendientes: 0,
    ...overrides,
  };
}

const NECESIDAD: Necesidad = {
  id: 1,
  organizacion_id: 1,
  categoria: 'alimento',
  descripcion: '50 kg de comida para perro adulto',
  estado: 'pendiente',
  creado_en: '2026-08-12T10:00:00',
  cubierta_en: null,
};

describe('SeccionNecesidades', () => {
  it('sin necesidades y sin ser el autor no renderiza nada', () => {
    const { container } = render(
      <SeccionNecesidades
        organizacion={crearOrganizacion()}
        necesidades={[]}
        onNecesidades={vi.fn()}
        esAutor={false}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('sin necesidades pero siendo el autor muestra el formulario para publicar la primera', () => {
    render(
      <SeccionNecesidades
        organizacion={crearOrganizacion()}
        necesidades={[]}
        onNecesidades={vi.fn()}
        esAutor
      />,
    );

    expect(screen.getByRole('heading', { name: 'Necesidades' })).toBeInTheDocument();
    expect(screen.getByLabelText('¿Qué necesitan?')).toBeInTheDocument();
  });

  it('con necesidades las lista aunque no seas el autor, sin acciones de escritura', () => {
    render(
      <SeccionNecesidades
        organizacion={crearOrganizacion({ user_id: 2 })}
        necesidades={[NECESIDAD]}
        onNecesidades={vi.fn()}
        esAutor={false}
      />,
    );

    expect(screen.getByText(/50 kg de comida/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Quiero ayudar' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Marcar cubierta' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('¿Qué necesitan?')).not.toBeInTheDocument();
  });
});
