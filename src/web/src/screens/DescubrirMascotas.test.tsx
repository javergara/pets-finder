import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation, useParams } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { Mascota } from '../api/types';
import { FILTROS_ADOPCION_DEFAULT } from '../lib/adopcion';
import { setActiveUserId } from '../lib/session';
import { DescubrirMascotas } from './DescubrirMascotas';

// Deck de descubrimiento (AD-03, paso 11).
//
// Lo que estos casos protegen, por orden de gravedad:
//
// 1. **Sin cuenta no se escribe nada a nombre de nadie.** `getActiveUserId()`
//    cae al `DEMO_USER_ID = 1`, que en producción es una persona real (Ana
//    Martínez): un swipe registrado sin cuenta quedaría a su nombre y le
//    ensuciaría el deck. Por eso hay un caso para el `like` (lleva al registro)
//    y otro para el `pass` (avanza en local, sin API), y otro más para la
//    llamada inicial, que no debe mandar `adoptante_id` inventado.
// 2. **La carta se quita en optimista y no vuelve.** Un fallo de red no la
//    repone y no dispara un refetch (`docs/conventions.md` §3): quien está
//    decidiendo con la mano en el teléfono no puede ver reaparecer la mascota
//    que acaba de pasar.
// 3. **Ver el deck nunca exige cuenta ni perfil de hogar**: sin afinidad se
//    invita a completarlo, pero el deck funciona igual.
// 4. **El "me interesa" avisa que salió una solicitud** (AD-05): sin ese acuse,
//    quien swipea no tiene forma de saber que acaba de pedir una mascota ni
//    dónde seguirla.

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, listarDeck: vi.fn(), registrarSwipe: vi.fn() };
});

function mascota(overrides: Partial<Mascota> = {}): Mascota {
  return {
    id: 7,
    organizacion_id: 2,
    user_id: null,
    report_id: null,
    nombre: 'Canela',
    especie: 'perro',
    raza: 'Cocker mestiza',
    sexo: 'hembra',
    edad_meses: 18,
    tamano: 'mediano',
    energia: 'media',
    fotos: ['/media/seed/pet_7.jpg'],
    historia: 'Rescatada en Armenia tras el sismo.',
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

const CON_AFINIDAD = {
  score: 94,
  explicacion: 'Encaja muy bien con tu hogar.',
  razones: [
    'Energía media, ideal para tus 6 horas fuera',
    'Tamaño adecuado para tu casa con patio',
  ],
  incompatible: false,
};

/** Dos cartas: la de arriba es Canela, la siguiente Rocky. Basta para ver que el
 * deck avanza sin volver a pedirle nada al backend. */
function dosMascotas(overrides: Partial<Mascota> = {}): Mascota[] {
  return [mascota(overrides), mascota({ id: 8, nombre: 'Rocky', sexo: 'macho', ...overrides })];
}

// Stubs que imprimen la ruta completa: el gate no solo tiene que redirigir, tiene
// que llevar el `?volver=` exacto para regresar al deck tras registrarse.
function RegistroStub() {
  const { pathname, search } = useLocation();
  return <p>{`registro ${pathname}${search}`}</p>;
}

function FichaStub() {
  const { id } = useParams<{ id: string }>();
  return <p>{`ficha de la mascota ${id}`}</p>;
}

function renderDeck() {
  return render(
    <MemoryRouter initialEntries={['/adoptar/descubrir']}>
      <Routes>
        <Route path="/adoptar/descubrir" element={<DescubrirMascotas />} />
        <Route path="/adoptar/mascota/:id" element={<FichaStub />} />
        <Route path="/registro" element={<RegistroStub />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.mocked(client.listarDeck).mockResolvedValue(dosMascotas());
  vi.mocked(client.registrarSwipe).mockResolvedValue({
    id: 1,
    user_id: 7,
    pet_id: 7,
    direccion: 'like',
    creado_en: '2026-08-15T10:00:00',
    solicitud: null,
  });
});

afterEach(() => {
  vi.resetAllMocks();
});

describe('DescubrirMascotas', () => {
  it('con cuenta pide el deck con el id de quien mira', async () => {
    setActiveUserId(7);

    renderDeck();

    expect(client.listarDeck).toHaveBeenCalledWith(7, FILTROS_ADOPCION_DEFAULT);
    expect(await screen.findByRole('heading', { name: 'Canela' })).toBeInTheDocument();
  });

  it('sin cuenta el deck se ve igual, pero no manda el id de nadie', async () => {
    renderDeck();

    expect(client.listarDeck).toHaveBeenCalledWith(undefined, FILTROS_ADOPCION_DEFAULT);
    expect(await screen.findByRole('heading', { name: 'Canela' })).toBeInTheDocument();
  });

  it('"Me interesa" registra el swipe y pasa a la siguiente sin volver a pedir el deck', async () => {
    setActiveUserId(7);
    renderDeck();
    await screen.findByRole('heading', { name: 'Canela' });

    fireEvent.click(screen.getByRole('button', { name: 'Me interesa' }));

    expect(await screen.findByRole('heading', { name: 'Rocky' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Canela' })).not.toBeInTheDocument();
    expect(client.registrarSwipe).toHaveBeenCalledWith(7, 7, 'like');
    // El deck que ya está en memoria alcanza: un refetch por swipe multiplicaría
    // las llamadas justo cuando la conexión es peor (emergencia, datos móviles).
    expect(client.listarDeck).toHaveBeenCalledTimes(1);
  });

  it('"Ahora no" registra el pass, que no rechaza a nadie (ADR 0002)', async () => {
    setActiveUserId(7);
    renderDeck();
    await screen.findByRole('heading', { name: 'Canela' });

    fireEvent.click(screen.getByRole('button', { name: 'Ahora no' }));

    expect(await screen.findByRole('heading', { name: 'Rocky' })).toBeInTheDocument();
    expect(client.registrarSwipe).toHaveBeenCalledWith(7, 7, 'pass');
  });

  it('si falla la red al registrar el swipe, la carta igual avanzó y la pantalla no se rompe', async () => {
    setActiveUserId(7);
    vi.mocked(client.registrarSwipe).mockRejectedValue(new client.ApiError('Sin conexión'));
    renderDeck();
    await screen.findByRole('heading', { name: 'Canela' });

    fireEvent.click(screen.getByRole('button', { name: 'Me interesa' }));

    expect(await screen.findByRole('heading', { name: 'Rocky' })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    // Ni se repone la carta ni se vuelve a pedir el deck: la decisión ya se tomó.
    expect(screen.queryByRole('heading', { name: 'Canela' })).not.toBeInTheDocument();
    expect(client.listarDeck).toHaveBeenCalledTimes(1);
  });

  it('sin cuenta, "Me interesa" lleva al registro y no escribe nada', async () => {
    renderDeck();
    await screen.findByRole('heading', { name: 'Canela' });

    fireEvent.click(screen.getByRole('button', { name: 'Me interesa' }));

    // El `?volver=` codificado: si se rompe, el registro no sabe adónde devolver.
    expect(
      await screen.findByText('registro /registro?volver=%2Fadoptar%2Fdescubrir'),
    ).toBeInTheDocument();
    expect(client.registrarSwipe).not.toHaveBeenCalled();
  });

  it('sin cuenta, "Ahora no" avanza el deck en local sin llamar a la API', async () => {
    renderDeck();
    await screen.findByRole('heading', { name: 'Canela' });

    fireEvent.click(screen.getByRole('button', { name: 'Ahora no' }));

    expect(await screen.findByRole('heading', { name: 'Rocky' })).toBeInTheDocument();
    expect(client.registrarSwipe).not.toHaveBeenCalled();
  });

  it('"Ver ficha" abre la mascota de arriba', async () => {
    renderDeck();
    await screen.findByRole('heading', { name: 'Canela' });

    fireEvent.click(screen.getByRole('button', { name: 'Ver ficha' }));

    expect(await screen.findByText('ficha de la mascota 7')).toBeInTheDocument();
  });

  it('al acabarse el deck ofrece la salida al catálogo', async () => {
    vi.mocked(client.listarDeck).mockResolvedValue([]);

    renderDeck();

    expect(await screen.findByText(/No quedan mascotas por ver/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ver el catálogo completo' })).toHaveAttribute(
      'href',
      '/adoptar',
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('cambiar un chip vuelve a pedir el deck con ese filtro', async () => {
    setActiveUserId(7);
    renderDeck();
    await screen.findByRole('heading', { name: 'Canela' });

    fireEvent.click(screen.getByRole('button', { name: 'Gato' }));

    await waitFor(() => expect(client.listarDeck).toHaveBeenCalledTimes(2));
    expect(client.listarDeck).toHaveBeenLastCalledWith(7, {
      ...FILTROS_ADOPCION_DEFAULT,
      especie: ['gato'],
    });
  });

  it('sin afinidad invita a completar el hogar, pero el deck sigue funcionando', async () => {
    setActiveUserId(7);
    renderDeck();
    await screen.findByRole('heading', { name: 'Canela' });

    expect(screen.getByText(/Mejora tus coincidencias/i)).toBeInTheDocument();
    // La invitación NO es un guard: se puede seguir decidiendo con ella en pantalla.
    fireEvent.click(screen.getByRole('button', { name: 'Me interesa' }));
    expect(await screen.findByRole('heading', { name: 'Rocky' })).toBeInTheDocument();
  });

  // ⚠️ Este caso **reemplaza** al de AD-03 ("la invitación todavía no es un
  // enlace"), que aseveraba justo lo contrario. No es que el test estuviera mal:
  // su premisa era que `/adoptar/mi-hogar` no existía y un link habría sido una
  // pantalla en blanco en producción entre los dos deploys. AD-04 crea la ruta,
  // así que la premisa dejó de ser cierta — mismo caso que los chips de edad en
  // AD-03. Sin el enlace la invitación no lleva a ninguna parte: hay que
  // adivinar la URL.
  it('la invitación lleva al cuestionario de hogar, ahora que la ruta existe', async () => {
    renderDeck();
    const invitacion = await screen.findByText(/Mejora tus coincidencias/i);

    const enlace = invitacion.closest('section')?.querySelector('a');
    expect(enlace).not.toBeNull();
    expect(enlace).toHaveAttribute('href', '/adoptar/mi-hogar');
  });

  it('con perfil de hogar muestra el porcentaje de afinidad y ya no invita', async () => {
    setActiveUserId(7);
    vi.mocked(client.listarDeck).mockResolvedValue(dosMascotas({ afinidad: CON_AFINIDAD }));

    renderDeck();

    expect(await screen.findByText('94% afín')).toBeInTheDocument();
    expect(screen.getByText(/Energía media, ideal para tus 6 horas fuera/)).toBeInTheDocument();
    expect(screen.queryByText(/Mejora tus coincidencias/i)).not.toBeInTheDocument();
  });

  // AD-05, paso 6. El swipe-derecha crea la solicitud en el backend y la
  // devuelve en `SwipeOut.solicitud`; el modal es el único acuse de recibo que
  // ve quien la envió. Sin él, "Me interesa" se siente igual que "Ahora no".
  it('"Me interesa" que crea solicitud la acusa con el nombre de la mascota', async () => {
    setActiveUserId(7);
    vi.mocked(client.registrarSwipe).mockResolvedValue({
      id: 1,
      user_id: 7,
      pet_id: 7,
      direccion: 'like',
      creado_en: '2026-08-15T10:00:00',
      solicitud: {
        id: 31,
        estado: 'solicitado',
        etiqueta: 'Sin responder · 0 días',
        creado_en: '2026-08-15T10:00:00',
        pet: {
          id: 7,
          nombre: 'Canela',
          especie: 'perro',
          raza: 'Cocker mestiza',
          edad_meses: 18,
          fotos: ['/media/seed/pet_7.jpg'],
          estado: 'disponible',
        },
      },
    });
    renderDeck();
    await screen.findByRole('heading', { name: 'Canela' });

    fireEvent.click(screen.getByRole('button', { name: 'Me interesa' }));

    const modal = await screen.findByRole('dialog');
    expect(modal).toHaveTextContent('Canela');
    expect(screen.getByRole('link', { name: 'Ver mis solicitudes' })).toHaveAttribute(
      'href',
      '/adoptar/mis-solicitudes',
    );
    // El deck sigue vivo detrás: cerrar el acuse devuelve a la carta siguiente.
    fireEvent.click(screen.getByRole('button', { name: 'Seguir viendo mascotas' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Rocky' })).toBeInTheDocument();
  });

  it('"Ahora no" no acusa nada: el pass no pide ninguna mascota', async () => {
    setActiveUserId(7);
    // El backend manda `solicitud: null` en el pass (el del `beforeEach`), así
    // que la pantalla no tiene nada que anunciar. Un modal aquí sería decirle a
    // alguien que pidió la mascota que acaba de descartar.
    renderDeck();
    await screen.findByRole('heading', { name: 'Canela' });

    fireEvent.click(screen.getByRole('button', { name: 'Ahora no' }));

    expect(await screen.findByRole('heading', { name: 'Rocky' })).toBeInTheDocument();
    expect(client.registrarSwipe).toHaveBeenCalledWith(7, 7, 'pass');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('mientras carga muestra el esqueleto anunciado como estado, no una pantalla vacía', () => {
    vi.mocked(client.listarDeck).mockReturnValue(new Promise(() => {}));

    renderDeck();

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('si el deck falla muestra un mensaje en español y quita el esqueleto', async () => {
    vi.mocked(client.listarDeck).mockRejectedValue(new client.ApiError('offline'));

    renderDeck();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /No pudimos cargar las mascotas para descubrir/i,
    );
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});
