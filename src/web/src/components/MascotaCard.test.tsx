import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import type { Mascota } from '../api/types';
import { MascotaCard } from './MascotaCard';

function mascota(overrides: Partial<Mascota> = {}): Mascota {
  return {
    id: 7,
    organizacion_id: 2,
    user_id: null,
    report_id: null,
    nombre: 'Nala',
    especie: 'perro',
    raza: 'Criolla',
    sexo: 'hembra',
    edad_meses: 18,
    tamano: 'mediano',
    energia: 'media',
    fotos: ['/media/seed/pet_7.jpg'],
    historia: 'Rescatada del barrio Providencia, duerme donde le pongan una cobija.',
    tags: ['cariñosa', 'buena con niños'],
    esterilizado: true,
    vacunas_al_dia: true,
    microchip: false,
    desparasitado: true,
    apto_ninos: true,
    apto_perros: true,
    apto_gatos: false,
    zona: 'Armenia',
    ciudad_texto: null,
    barrio: 'Providencia',
    lat: 4.53,
    lng: -75.68,
    telefono_contacto: null,
    estado: 'disponible',
    publicado_en: '2026-08-14T10:00:00',
    adoptado_en: null,
    publicador: null,
    afinidad: null,
    es_favorito: false,
    ya_solicitada: false,
    distancia_km: null,
    ...overrides,
  };
}

/** Imprime la ruta actual del router de prueba. El corazón vive DENTRO de un
 * `<Link>` que ocupa la tarjeta entera, así que "no navegó" hay que aseverarlo
 * sobre la ubicación real: mirar solo que el handler se llamó pasaría igual
 * aunque el clic se llevara a la persona a la ficha. */
function Ubicacion() {
  const { pathname } = useLocation();
  return <p>{`ubicación ${pathname}`}</p>;
}

function renderCard(datos: Mascota, onAlternarFavorita?: () => void) {
  return render(
    <MemoryRouter initialEntries={['/adoptar']}>
      <Ubicacion />
      <MascotaCard mascota={datos} onAlternarFavorita={onAlternarFavorita} />
    </MemoryRouter>,
  );
}

describe('MascotaCard', () => {
  it('muestra el nombre, la edad legible y los tags', () => {
    renderCard(mascota());

    expect(screen.getByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    // 18 meses se dicen "1 año" (edadLegible trunca), nunca "2 años" ni "0 años".
    expect(screen.getByText(/1 año/)).toBeInTheDocument();
    expect(screen.getByText('cariñosa')).toBeInTheDocument();
    expect(screen.getByText('buena con niños')).toBeInTheDocument();
  });

  it('muestra la raza y la zona', () => {
    renderCard(mascota());

    expect(screen.getByText(/Criolla/)).toBeInTheDocument();
    expect(screen.getByText('Armenia')).toBeInTheDocument();
  });

  it('no rompe la tarjeta con muchos tags: muestra como mucho tres', () => {
    renderCard(mascota({ tags: ['uno', 'dos', 'tres', 'cuatro', 'cinco'] }));

    expect(screen.getByText('tres')).toBeInTheDocument();
    expect(screen.queryByText('cuatro')).not.toBeInTheDocument();
    expect(screen.queryByText('cinco')).not.toBeInTheDocument();
  });

  it('la foto carga en diferido y su alt menciona el nombre', () => {
    renderCard(mascota());

    const foto = screen.getByRole('img');
    expect(foto).toHaveAttribute('loading', 'lazy');
    expect(foto.getAttribute('alt')).toContain('Nala');
    // La ruta relativa pasa por mediaUrl (en test la base de la API es absoluta).
    expect(foto.getAttribute('src')).toContain('/media/seed/pet_7.jpg');
  });

  it('toda la tarjeta es un link a la ficha de la mascota', () => {
    renderCard(mascota({ id: 42 }));

    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/adoptar/mascota/42');
    expect(link).toHaveTextContent('Nala');
  });

  it.each([
    ['disponible' as const, 'En adopción'],
    ['en_proceso' as const, 'En proceso'],
    ['adoptado' as const, 'Adoptada 💚'],
  ])('el badge de estado %s dice "%s"', (estado, copy) => {
    renderCard(mascota({ estado }));

    expect(screen.getByText(copy)).toBeInTheDocument();
  });

  it('sin afinidad no muestra el porcentaje (en AD-01 siempre es null)', () => {
    renderCard(mascota());

    expect(screen.queryByText(/% afín/)).not.toBeInTheDocument();
  });

  it('con afinidad muestra el score', () => {
    renderCard(
      mascota({
        afinidad: {
          score: 88,
          explicacion: 'Encaja con tu hogar',
          razones: [],
          incompatible: false,
        },
      }),
    );

    expect(screen.getByText('88% afín')).toBeInTheDocument();
  });

  it('una mascota sin fotos se sigue viendo entera', () => {
    renderCard(mascota({ fotos: [] }));

    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    expect(screen.getByRole('link')).toHaveAttribute('href', '/adoptar/mascota/7');
  });

  // ── El corazón (AD-07) ─────────────────────────────────────────────────────
  describe('corazón de favoritos', () => {
    it('sin la prop no pinta ningún corazón (no un corazón muerto)', () => {
      renderCard(mascota());

      // `PanelAdopcionOrganizacion` usa esta misma tarjeta y no tiene favoritos:
      // un botón que no guarda nada es peor que ningún botón.
      expect(screen.queryByRole('button')).not.toBeInTheDocument();
      expect(screen.queryByText('♡')).not.toBeInTheDocument();
      expect(screen.queryByText('♥')).not.toBeInTheDocument();
    });

    it('con la prop, el clic en el corazón guarda y NO navega a la ficha', () => {
      const alternar = vi.fn();
      renderCard(mascota(), alternar);

      const noCancelado = fireEvent.click(
        screen.getByRole('button', { name: 'Guardar en favoritos' }),
      );

      expect(alternar).toHaveBeenCalledTimes(1);
      // Dos aserciones porque son dos navegaciones distintas, y una sola no
      // basta:
      //
      // 1. La ubicación cubre la del router: sin el handler propio, el `onClick`
      //    del `<Link>` correría y la persona acabaría en la ficha.
      // 2. `fireEvent.click` devuelve `false` solo si alguien canceló el evento,
      //    y eso es lo único que aquí prueba el `preventDefault`: lo que ese
      //    `preventDefault` frena es la navegación NATIVA del `<a href>` —una
      //    recarga entera de la página en un navegador de verdad—, que jsdom no
      //    simula y por eso jamás aparecería en la ubicación de arriba.
      expect(screen.getByText('ubicación /adoptar')).toBeInTheDocument();
      expect(noCancelado).toBe(false);
    });

    it('el resto de la tarjeta sigue navegando a la ficha', () => {
      const alternar = vi.fn();
      renderCard(mascota({ id: 42 }), alternar);

      fireEvent.click(screen.getByRole('heading', { name: 'Nala' }));

      expect(screen.getByText('ubicación /adoptar/mascota/42')).toBeInTheDocument();
      expect(alternar).not.toHaveBeenCalled();
    });

    it('ya guardada, el corazón invita a quitarla', () => {
      renderCard(mascota({ es_favorito: true }), vi.fn());

      expect(screen.getByRole('button', { name: 'Quitar de favoritos' })).toBeInTheDocument();
      expect(
        screen.queryByRole('button', { name: 'Guardar en favoritos' }),
      ).not.toBeInTheDocument();
    });
  });
});
