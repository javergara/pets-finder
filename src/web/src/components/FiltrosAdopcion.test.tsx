import { fireEvent, render, screen } from '@testing-library/react';
import type { FiltrosMascotas } from '../api/client';
import { describe, expect, it, vi } from 'vitest';
import { FILTROS_ADOPCION_DEFAULT } from '../lib/adopcion';
import { FiltrosAdopcion } from './FiltrosAdopcion';

// El plegado móvil de los filtros (AD-08 paso 7), probado donde vive: dentro del
// componente, que es el único sitio del repo que lo implementa para sus dos
// pantallas (`CatalogoAdopcion` y `DescubrirMascotas`).
//
// ⚠️ **En jsdom el panel arranca SIEMPRE plegado**, y no por casualidad: jsdom
// (29.1.1) no implementa `window.matchMedia`, así que la consulta de ≥1024px del
// estado inicial da `false`. Eso es exactamente el caso que hay que proteger —el
// móvil de 360px del acceptance—, y en Chrome de escritorio el mismo código da
// `true` y el panel se pinta desplegado como siempre.
//
// ⚠️ Los casos aseveran que el panel **no está en el DOM**, no que esté oculto.
// Es deliberado: en jsdom no hay CSS, así que un `class="hidden"` no ocultaría
// nada y un test escrito sobre visibilidad pasaría con el panel a la vista en el
// móvil real (el género de test decorativo de `memory/memory.md`, 2026-08-16).
// `document.getElementById` es la comprobación más cruda posible y por eso es la
// que se usa: ninguna clase de Tailwind puede engañarla.

function renderFiltros(filtros: Partial<FiltrosMascotas> = {}) {
  const onChange = vi.fn();
  const onReset = vi.fn();
  render(
    <FiltrosAdopcion
      filtros={{ ...FILTROS_ADOPCION_DEFAULT, ...filtros }}
      onChange={onChange}
      onReset={onReset}
    />,
  );
  return { onChange, onReset };
}

/** El botón plegable: su nombre accesible empieza por "Filtros" y lleva dentro
 * el contador, así que se busca por prefijo y no por texto exacto. */
function botonFiltros() {
  return screen.getByRole('button', { name: /^Filtros/ });
}

describe('FiltrosAdopcion — plegado en móvil', () => {
  it('arranca plegado: el panel no está en el DOM y el botón lo dice', () => {
    renderFiltros();

    expect(botonFiltros()).toHaveAttribute('aria-expanded', 'false');
    expect(document.getElementById('filtros-adopcion')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Perro' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Zona')).not.toBeInTheDocument();
  });

  it('pulsar el botón despliega los chips y la zona', () => {
    renderFiltros();

    fireEvent.click(botonFiltros());

    expect(botonFiltros()).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('button', { name: 'Perro' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cachorra' })).toBeInTheDocument();
    expect(screen.getByLabelText('Zona')).toBeInTheDocument();
  });

  it('volver a pulsarlo lo pliega y el panel desaparece del DOM otra vez', () => {
    renderFiltros();

    fireEvent.click(botonFiltros());
    expect(document.getElementById('filtros-adopcion')).not.toBeNull();

    fireEvent.click(botonFiltros());

    expect(document.getElementById('filtros-adopcion')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Perro' })).not.toBeInTheDocument();
  });

  // Sin `aria-controls` apuntando a un id real, quien navega con lector de
  // pantalla oye "contraído" pero no tiene forma de saber qué se contrajo.
  it('el aria-controls del botón apunta al panel que despliega', () => {
    renderFiltros();

    expect(botonFiltros()).toHaveAttribute('aria-controls', 'filtros-adopcion');

    fireEvent.click(botonFiltros());

    const panel = document.getElementById('filtros-adopcion');
    expect(panel).not.toBeNull();
    expect(panel).toContainElement(screen.getByRole('button', { name: 'Perro' }));
  });

  // ⚠️ El contador es lo que impide que plegar el panel **esconda un filtro
  // activo en silencio**: con los chips fuera de la pantalla, el número del
  // botón es la única señal de que el catálogo está recortado. Sin él, quien ve
  // pocas mascotas creería que no hay más.
  it('sin filtros puestos el botón dice solo "Filtros"', () => {
    renderFiltros();

    expect(botonFiltros()).toHaveAccessibleName('Filtros');
  });

  it('plegado, el botón cuenta los filtros puestos', () => {
    renderFiltros({ especie: ['perro'], zona: 'Cali' });

    expect(botonFiltros()).toHaveAccessibleName('Filtros · 2');
  });

  // El grupo que el `hayFiltros` del catálogo se saltaba (el bug de este paso):
  // si el contador lo olvidara, un tramo de edad activo sería invisible con el
  // panel cerrado.
  it('el contador incluye el tramo de edad', () => {
    renderFiltros({ edad: ['cachorro'] });

    expect(botonFiltros()).toHaveAccessibleName('Filtros · 1');
  });

  // "Limpiar filtros" vive dentro del panel: aparece al desplegarlo, no antes.
  it('desplegado con filtros puestos ofrece limpiarlos', () => {
    const { onReset } = renderFiltros({ especie: ['perro'] });

    fireEvent.click(botonFiltros());
    fireEvent.click(screen.getByRole('button', { name: 'Limpiar filtros' }));

    expect(onReset).toHaveBeenCalledTimes(1);
  });
});
