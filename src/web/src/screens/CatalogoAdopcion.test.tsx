import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Mascota } from '../api/types';
import { FILTROS_ADOPCION_DEFAULT } from '../lib/adopcion';
import { setActiveUserId } from '../lib/session';
import { CatalogoAdopcion } from './CatalogoAdopcion';

// ⚠️ Desde AD-07 el catálogo llama a `listarMascotas` SIEMPRE con dos
// argumentos: los filtros y el adoptante, que es `undefined` sin cuenta. Por eso
// cada aserción de este archivo nombra el segundo argumento — `undefined` ahí no
// es ruido, es el caso anónimo escrito a la vista (mismo criterio que
// `DescubrirMascotas.test.tsx` con `listarDeck`).

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return {
    ...actual,
    listarMascotas: vi.fn(),
    obtenerAdopcionesResumen: vi.fn(),
    marcarFavorita: vi.fn(),
    desmarcarFavorita: vi.fn(),
  };
});

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
    historia: 'Rescatada del barrio Providencia.',
    tags: ['cariñosa'],
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

beforeEach(() => {
  vi.mocked(client.listarMascotas).mockResolvedValue([
    mascota(),
    mascota({ id: 8, nombre: 'Copito', especie: 'gato', tamano: 'pequeño' }),
  ]);
  vi.mocked(client.obtenerAdopcionesResumen).mockResolvedValue({ total: 0, recientes: [] });
  vi.mocked(client.marcarFavorita).mockResolvedValue(mascota({ es_favorito: true }));
  vi.mocked(client.desmarcarFavorita).mockResolvedValue(undefined);
});

afterEach(() => {
  vi.resetAllMocks();
});

/** Stub que imprime la ruta completa: el gate del corazón no solo tiene que
 * redirigir, tiene que llevar el `?volver=` exacto para regresar al catálogo. */
function RegistroStub() {
  const { pathname, search } = useLocation();
  return <p>{`registro ${pathname}${search}`}</p>;
}

/** Despliega el panel de filtros antes de tocar un chip o la zona.
 *
 * ⚠️ **Premisa caducada a propósito** (AD-08 paso 7), igual que el caso de los
 * chips de edad de más abajo: hasta ahora los chips estaban en el documento al
 * montar. Desde el plegado móvil de `FiltrosAdopcion` el panel **se desmonta**
 * mientras está cerrado, y en jsdom siempre arranca cerrado (no implementa
 * `window.matchMedia`, así que la consulta de ≥1024px da `false`). Los casos que
 * filtran tienen que abrirlo primero, que es lo que hace una persona en el
 * móvil; lo que protegen —qué se manda a la API y qué chip queda presionado— no
 * cambia ni una línea. */
function abrirFiltros() {
  fireEvent.click(screen.getByRole('button', { name: /^Filtros/ }));
}

function renderCatalogo() {
  return render(
    <MemoryRouter initialEntries={['/adoptar']}>
      <Routes>
        <Route path="/adoptar" element={<CatalogoAdopcion />} />
        <Route path="/registro" element={<RegistroStub />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('CatalogoAdopcion', () => {
  it('al montar pide el catálogo con los filtros por defecto y pinta las tarjetas', async () => {
    renderCatalogo();

    expect(client.listarMascotas).toHaveBeenCalledWith(FILTROS_ADOPCION_DEFAULT, undefined);
    expect(await screen.findByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Copito' })).toBeInTheDocument();
  });

  it('el chip "Perro" filtra por especie y queda marcado como presionado', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    abrirFiltros();
    const chipPerro = screen.getByRole('button', { name: 'Perro' });
    expect(chipPerro).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(chipPerro);

    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(2));
    expect(client.listarMascotas).toHaveBeenLastCalledWith(
      { ...FILTROS_ADOPCION_DEFAULT, especie: ['perro'] },
      undefined,
    );
    expect(screen.getByRole('button', { name: 'Perro' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('un segundo chip de la misma familia acumula en vez de reemplazar', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    abrirFiltros();
    fireEvent.click(screen.getByRole('button', { name: 'Perro' }));
    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(2));
    fireEvent.click(screen.getByRole('button', { name: 'Gato' }));

    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(3));
    expect(client.listarMascotas).toHaveBeenLastCalledWith(
      { ...FILTROS_ADOPCION_DEFAULT, especie: ['perro', 'gato'] },
      undefined,
    );
    expect(screen.getByRole('button', { name: 'Perro' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Gato' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('la zona es un control de valor único', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    abrirFiltros();
    fireEvent.change(screen.getByLabelText('Zona'), { target: { value: 'Cali' } });

    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(2));
    expect(client.listarMascotas).toHaveBeenLastCalledWith(
      { ...FILTROS_ADOPCION_DEFAULT, zona: 'Cali' },
      undefined,
    );
  });

  it('"Limpiar filtros" vuelve a los valores por defecto', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    abrirFiltros();
    fireEvent.click(screen.getByRole('button', { name: 'Perro' }));
    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(2));

    // El panel sigue desplegado: tocar un chip no lo pliega (quien filtra suele
    // encadenar varios), así que "Limpiar filtros" está a la vista.
    fireEvent.click(screen.getByRole('button', { name: 'Limpiar filtros' }));

    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(3));
    expect(client.listarMascotas).toHaveBeenLastCalledWith(FILTROS_ADOPCION_DEFAULT, undefined);
    expect(screen.getByRole('button', { name: 'Perro' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('sin resultados muestra un estado vacío con su CTA, no el esqueleto de carga', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([]);

    renderCatalogo();

    expect(await screen.findByText(/Todavía no hay mascotas/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /centros de ayuda/i })).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('el CTA del estado vacío lleva a publicar una mascota, no a los centros de ayuda (AD-02)', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([]);

    renderCatalogo();

    expect(
      await screen.findByRole('link', { name: 'Publicar una mascota en adopción' }),
    ).toHaveAttribute('href', '/adoptar/publicar');
  });

  it('el header ofrece siempre la entrada a publicar (AD-02)', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    expect(screen.getByRole('link', { name: 'Dar en adopción' })).toHaveAttribute(
      'href',
      '/adoptar/publicar',
    );
  });

  // El deck (AD-03) no se anuncia en la nav hasta AD-08: esta es su única puerta
  // de entrada, así que el href tiene que ser exacto o la pantalla queda huérfana.
  it('el header lleva al deck de descubrimiento (AD-03)', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    expect(screen.getByRole('link', { name: 'Descubrir una por una' })).toHaveAttribute(
      'href',
      '/adoptar/descubrir',
    );
  });

  // Sin esto, el cuestionario solo se alcanza desde la invitación del deck — y
  // esa invitación desaparece justo cuando ya lo contestaste, que es cuando hace
  // falta para cambiar una respuesta. La ruta quedaría solo para quien recuerde
  // la URL.
  it('el header ofrece entrar al cuestionario de hogar para reeditarlo (AD-04)', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    expect(screen.getByRole('link', { name: 'Mi hogar' })).toHaveAttribute(
      'href',
      '/adoptar/mi-hogar',
    );
  });

  // Igual que el deck y el cuestionario: "Mis solicitudes" (AD-05) no está en la
  // nav hasta AD-08, así que sin esta entrada la pantalla solo se alcanza desde
  // el acuse de un swipe — y ese modal se cierra y no vuelve.
  it('el header lleva a las solicitudes propias (AD-05)', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    expect(screen.getByRole('link', { name: 'Mis solicitudes' })).toHaveAttribute(
      'href',
      '/adoptar/mis-solicitudes',
    );
  });

  // Misma razón que "Mis solicitudes", y con un agravante: la lista guardada no
  // se alcanza desde ningún otro sitio —el corazón guarda pero no lleva a
  // ninguna parte—, así que sin esta entrada los favoritos serían una función
  // que se usa a ciegas y nunca se puede revisar.
  it('el header lleva a las mascotas guardadas (AD-07)', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    expect(screen.getByRole('link', { name: 'Mis favoritas' })).toHaveAttribute(
      'href',
      '/adoptar/mis-favoritas',
    );
  });

  it('si la API falla muestra un mensaje en español y quita el esqueleto', async () => {
    vi.mocked(client.listarMascotas).mockRejectedValue(new Error('offline'));

    renderCatalogo();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /No pudimos cargar las mascotas en adopción/i,
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('la franja de adopciones logradas aparece cuando hay al menos una', async () => {
    vi.mocked(client.obtenerAdopcionesResumen).mockResolvedValue({
      total: 3,
      recientes: [
        {
          id: 4,
          nombre: 'Pelusa',
          especie: 'gato',
          raza: null,
          edad_meses: 24,
          fotos: ['/media/seed/pet_4.jpg'],
          estado: 'adoptado',
        },
      ],
    });

    renderCatalogo();

    expect(await screen.findByText('3')).toBeInTheDocument();
    expect(screen.getByText(/adopciones logradas/i)).toBeInTheDocument();
  });

  it('sin adopciones todavía, la franja no se muestra (nunca un cero triste)', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    expect(screen.queryByText(/adopciones logradas/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/adopción lograda/i)).not.toBeInTheDocument();
  });

  // Este caso reemplaza al que aseveraba que NO había chips de edad. Su premisa
  // ("el backend los ignora") dejó de ser cierta en el paso 5 de AD-03, cuando
  // `GET /api/pets` empezó a traducir `edad_categoria` a SQL: mantenerlo sería
  // fijar por test una limitación que ya no existe.
  it('el chip "Cachorra" filtra por tramo de edad y queda marcado como presionado', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    abrirFiltros();
    const chipCachorra = screen.getByRole('button', { name: 'Cachorra' });
    expect(chipCachorra).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(chipCachorra);

    await waitFor(() => expect(client.listarMascotas).toHaveBeenCalledTimes(2));
    expect(client.listarMascotas).toHaveBeenLastCalledWith(
      { ...FILTROS_ADOPCION_DEFAULT, edad: ['cachorro'] },
      undefined,
    );
    expect(screen.getByRole('button', { name: 'Cachorra' })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });

  // ⚠️ Bug real, encontrado al extraer `contarFiltrosActivos` (AD-08 paso 7): el
  // `hayFiltros` de esta pantalla miraba especie, tamaño, energía y zona, y **se
  // saltaba la edad**. Con un tramo de edad como único filtro y cero resultados,
  // el vacío decía "Todavía no hay mascotas publicadas en adopción": le contaba a
  // la persona que el catálogo estaba vacío cuando lo que pasaba es que su filtro
  // no casaba — y encima le ofrecía publicar una mascota en vez de la salida que
  // necesitaba, que es quitar el filtro.
  it('con solo un tramo de edad y cero resultados, el vacío dice que es por los filtros', async () => {
    vi.mocked(client.listarMascotas).mockResolvedValue([]);
    renderCatalogo();
    await screen.findByText(/Todavía no hay mascotas/i);

    abrirFiltros();
    fireEvent.click(screen.getByRole('button', { name: 'Cachorra' }));

    expect(
      await screen.findByText(/Ninguna mascota coincide con estos filtros/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Todavía no hay mascotas/i)).not.toBeInTheDocument();
    // La salida correcta con filtros puestos es quitarlos, no publicar.
    expect(screen.getByRole('button', { name: 'Ver todas las mascotas' })).toBeInTheDocument();
  });

  // ── Filtros plegados en móvil (AD-08 paso 7) ───────────────────────────────
  // Primera mitad del acceptance de los 360px. La segunda ("la primera tarjeta
  // se ve sin scroll") **no se puede probar aquí**: jsdom no tiene motor de
  // layout y `getBoundingClientRect()` devuelve ceros, así que un test de altura
  // sería decorativo. Esa mitad se mide en Chrome real (paso 8).
  it('al montar, los chips no están en el documento: la rejilla empieza arriba', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    expect(screen.getByRole('button', { name: /^Filtros/ })).toHaveAttribute(
      'aria-expanded',
      'false',
    );
    expect(screen.queryByRole('button', { name: 'Perro' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Cachorra' })).not.toBeInTheDocument();
  });

  // ── GUARDA DE CLASE, NO DE LAYOUT (AD-08 paso 8) ───────────────────────────
  // Lo que este caso NO hace: comprobar que la página quepa en 360px. jsdom no
  // tiene motor de layout, `getBoundingClientRect()` devuelve ceros y ningún
  // test unitario puede medir un desborde. Esa mitad del acceptance se midió en
  // Chrome real: la fila de píldoras llevaba `shrink-0`, que como item flex la
  // fijaba a su ancho de contenido (705px) y dejaba su propio `flex-wrap` sin
  // efecto → `documentElement.scrollWidth` = 729 contra `clientWidth` = 360.
  // Quitando `shrink-0`: fila de 312px y scrollWidth = clientWidth = 360.
  // Lo que este caso SÍ hace: impedir que alguien reponga esa combinación de
  // clases, que es la causa exacta del bug. Si vuelve, salta aquí; si el
  // desborde llega por otro camino (una píldora más ancha, otro contenedor),
  // este caso seguirá verde. La comprobación de verdad es el navegador.
  it('la fila de píldoras del header no combina shrink-0 con flex-wrap (clases, no layout)', async () => {
    renderCatalogo();
    await screen.findByRole('heading', { name: 'Nala' });

    const fila = screen.getByRole('link', { name: 'Descubrir una por una' }).parentElement;
    // Anti-falso-verde: si la cabecera se reestructura y este `parentElement`
    // deja de ser la fila de píldoras, el caso falla aquí en vez de aprobar las
    // clases de un elemento cualquiera.
    for (const nombre of ['Mi hogar', 'Mis solicitudes', 'Mis favoritas', 'Dar en adopción']) {
      expect(fila).toContainElement(screen.getByRole('link', { name: nombre }));
    }

    expect(fila).toHaveClass('flex-wrap');
    expect(fila).not.toHaveClass('shrink-0');
  });

  // ── Favoritos (AD-07) ──────────────────────────────────────────────────────
  // Los dos riesgos de esta pantalla, por gravedad:
  //
  // 1. **Mandar `adoptante_id` sin cuenta.** `getActiveUserId()` cae al
  //    `DEMO_USER_ID = 1`, que en producción es una persona real (Ana Martínez):
  //    un visitante anónimo vería SUS favoritos pintados como propios y, al
  //    tocar el corazón, se los borraría.
  // 2. **Guardar navegando.** La tarjeta entera es un `<Link>`; el corazón vive
  //    dentro. Sin `preventDefault` el gesto de guardar saca a la persona del
  //    catálogo (ese candado vive en `MascotaCard.test.tsx`, que es donde está
  //    el código).
  describe('corazón de favoritos', () => {
    it('con cuenta, el catálogo pide el listado con el id de quien mira', async () => {
      setActiveUserId(7);

      renderCatalogo();

      expect(client.listarMascotas).toHaveBeenCalledWith(FILTROS_ADOPCION_DEFAULT, 7);
      expect(await screen.findByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    });

    it('sin cuenta NO manda adoptante_id (el fallback es una persona real)', async () => {
      renderCatalogo();

      expect(client.listarMascotas).toHaveBeenCalledWith(FILTROS_ADOPCION_DEFAULT, undefined);
      expect(await screen.findByRole('heading', { name: 'Nala' })).toBeInTheDocument();
    });

    it('sin cuenta el corazón se pinta igual, pero lleva al registro sin llamar a la API', async () => {
      renderCatalogo();
      await screen.findByRole('heading', { name: 'Nala' });

      const corazones = screen.getAllByRole('button', { name: 'Guardar en favoritos' });
      // Se pinta a propósito: esconderlo ocultaría que los favoritos existen.
      expect(corazones).toHaveLength(2);

      fireEvent.click(corazones[0]);

      // El orden importa: lo grave no es dejar de navegar, es escribir. Sin el
      // gate, esta llamada saldría con el `DEMO_USER_ID = 1` y guardaría la
      // mascota en la lista de una persona real.
      expect(client.marcarFavorita).not.toHaveBeenCalled();
      expect(client.desmarcarFavorita).not.toHaveBeenCalled();
      // El `?volver=` codificado: si se rompe, el registro no sabe adónde
      // devolver a quien acaba de crear la cuenta para guardar una mascota.
      expect(await screen.findByText('registro /registro?volver=%2Fadoptar')).toBeInTheDocument();
    });

    it('con cuenta, guarda y el corazón queda lleno al instante (sin re-consultar)', async () => {
      setActiveUserId(7);
      renderCatalogo();
      await screen.findByRole('heading', { name: 'Nala' });

      fireEvent.click(screen.getAllByRole('button', { name: 'Guardar en favoritos' })[0]);

      expect(client.marcarFavorita).toHaveBeenCalledWith(7, 7);
      // Optimista: la tarjeta cambia sin esperar la respuesta y sin refetch del
      // catálogo (`docs/conventions.md` §3).
      expect(
        await screen.findByRole('button', { name: 'Quitar de favoritos' }),
      ).toBeInTheDocument();
      expect(screen.getAllByRole('button', { name: 'Guardar en favoritos' })).toHaveLength(1);
      expect(client.listarMascotas).toHaveBeenCalledTimes(1);
    });

    it('con cuenta, tocar una ya guardada la quita', async () => {
      setActiveUserId(7);
      vi.mocked(client.listarMascotas).mockResolvedValue([mascota({ es_favorito: true })]);
      renderCatalogo();
      await screen.findByRole('heading', { name: 'Nala' });

      fireEvent.click(screen.getByRole('button', { name: 'Quitar de favoritos' }));

      expect(client.desmarcarFavorita).toHaveBeenCalledWith(7, 7);
      expect(client.marcarFavorita).not.toHaveBeenCalled();
      expect(
        await screen.findByRole('button', { name: 'Guardar en favoritos' }),
      ).toBeInTheDocument();
    });

    it('si la API falla, el catálogo no muestra error ni repone la tarjeta', async () => {
      setActiveUserId(7);
      vi.mocked(client.marcarFavorita).mockRejectedValue(new Error('offline'));
      renderCatalogo();
      await screen.findByRole('heading', { name: 'Nala' });

      fireEvent.click(screen.getAllByRole('button', { name: 'Guardar en favoritos' })[0]);

      expect(
        await screen.findByRole('button', { name: 'Quitar de favoritos' }),
      ).toBeInTheDocument();
      // El `act` vacío NO es ceremonia: sin él este caso es decorativo. Lo que se
      // asevera es que *nada cambia* — el corazón ya está lleno desde el clic
      // optimista —, así que un `.catch` que lo revirtiera volcaría su `setState`
      // DESPUÉS de que `findByRole` haya pasado en su primera comprobación. Medido:
      // con `findByRole` a secas la mutación sobrevive; con el `act` cae.
      await act(async () => {});
      expect(screen.getByRole('button', { name: 'Quitar de favoritos' })).toBeInTheDocument();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });
});
