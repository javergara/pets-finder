import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  agendarVisita,
  ApiError,
  aprobarSolicitud,
  crearMascota,
  descartarSolicitud,
  desmarcarFavorita,
  editarMascota,
  eliminarMascota,
  listarDeck,
  listarFavoritas,
  listarMascotas,
  listarSolicitudes,
  marcarFavorita,
  mediaUrl,
  guardarPerfilHogar,
  obtenerAdopcionesResumen,
  obtenerPerfilHogar,
  obtenerMascota,
  obtenerSolicitud,
  pedirInformacion,
  registrarSwipe,
} from './client';
import type { MascotaIn, PerfilHogarIn } from './types';

describe('mediaUrl', () => {
  it('prefija las rutas relativas con la base de la API (fotos locales del seed/dev)', () => {
    expect(mediaUrl('/media/seed/report_1.jpg')).toBe(
      'http://127.0.0.1:8000/media/seed/report_1.jpg',
    );
  });

  it('devuelve las URLs absolutas tal cual (fotos en Supabase Storage, ADR 0006)', () => {
    const absoluta = 'https://abc123.supabase.co/storage/v1/object/public/fotos/x.jpg';
    expect(mediaUrl(absoluta)).toBe(absoluta);
  });
});

// ── Adopción (AD-01) ─────────────────────────────────────────────────────────
// Lo que se prueba aquí es la URL que sale, no la respuesta: el riesgo real del
// módulo es armar mal la query (multi-selección colapsada, o el adoptante
// filtrando como si fuera el autor).

/** Espía de `fetch` que devuelve el cuerpo dado y captura la URL pedida. */
function espiarFetch(cuerpo: unknown = []) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => cuerpo,
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

/** Espía de `fetch` con la respuesta vacía real de un 204: `.json()` sobre un
 * cuerpo vacío lanza, así que este doble falla si el cliente intenta parsearlo. */
function espiarFetch204() {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 204,
    json: async () => {
      throw new SyntaxError('Unexpected end of JSON input');
    },
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

/** Espía de `fetch` que devuelve un error del backend con su `detail` en español. */
function espiarFetchError(status: number, detail: string) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: async () => ({ detail }),
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function urlPedida(fetchMock: ReturnType<typeof espiarFetch>): string {
  return String(fetchMock.mock.calls[0][0]);
}

function initPedido(fetchMock: ReturnType<typeof espiarFetch>): RequestInit {
  return fetchMock.mock.calls[0][1] as RequestInit;
}

/** El body tal como sale por el cable, ya parseado. */
function bodyEnviado(fetchMock: ReturnType<typeof espiarFetch>): Record<string, unknown> {
  return JSON.parse(String(initPedido(fetchMock).body)) as Record<string, unknown>;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('listarMascotas', () => {
  it('manda cada valor elegido como param repetido, no colapsado en uno', async () => {
    const fetchMock = espiarFetch();

    await listarMascotas({ especie: ['perro', 'gato'], tamano: ['grande'] });

    const url = new URL(urlPedida(fetchMock));
    expect(url.pathname).toBe('/api/pets');
    // `params.set` habría dejado especie=gato a secas: la multi-selección se
    // perdería en silencio y el catálogo mostraría solo la última opción.
    expect(url.searchParams.getAll('especie')).toEqual(['perro', 'gato']);
    expect(url.searchParams.getAll('tamano')).toEqual(['grande']);
    expect(url.search).toBe('?especie=perro&especie=gato&tamano=grande');
  });

  it('sin filtros pega al endpoint pelado, sin query basura', async () => {
    const fetchMock = espiarFetch();

    await listarMascotas();

    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/pets');
  });

  it('los arrays vacíos y la zona vacía no dejan claves sueltas', async () => {
    const fetchMock = espiarFetch();

    await listarMascotas({ especie: [], tamano: [], energia: [], edad: [], zona: '' });

    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/pets');
  });

  it('distingue quién publicó (user_id) de quién mira (adoptante_id)', async () => {
    const fetchMock = espiarFetch();

    await listarMascotas({ publicadaPorUserId: 4, estado: 'todos', organizacionId: 2 }, 7);

    const url = new URL(urlPedida(fetchMock));
    expect(url.searchParams.get('user_id')).toBe('4');
    expect(url.searchParams.get('adoptante_id')).toBe('7');
    expect(url.searchParams.get('organizacion_id')).toBe('2');
    expect(url.searchParams.get('estado')).toBe('todos');
  });

  it('el tramo de edad viaja como edad_categoria y la zona como zona', async () => {
    const fetchMock = espiarFetch();

    await listarMascotas({ edad: ['cachorro', 'senior'], energia: ['baja'], zona: 'Armenia' });

    const url = new URL(urlPedida(fetchMock));
    expect(url.searchParams.getAll('edad_categoria')).toEqual(['cachorro', 'senior']);
    expect(url.searchParams.getAll('energia')).toEqual(['baja']);
    expect(url.searchParams.get('zona')).toBe('Armenia');
  });
});

describe('obtenerMascota', () => {
  it('lleva el adoptante que mira como adoptante_id', async () => {
    const fetchMock = espiarFetch({ id: 3 });

    await obtenerMascota(3, 7);

    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/pets/3?adoptante_id=7');
  });

  it('sin adoptante no añade el param (la ficha es pública)', async () => {
    const fetchMock = espiarFetch({ id: 3 });

    await obtenerMascota(3);

    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/pets/3');
  });
});

describe('obtenerAdopcionesResumen', () => {
  it('pega a la ruta literal /adopciones, no a la dinámica /{id}', async () => {
    const fetchMock = espiarFetch({ total: 0, recientes: [] });

    await obtenerAdopcionesResumen();

    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/pets/adopciones');
  });
});

// ── Escrituras de adopción (AD-02) ───────────────────────────────────────────
// Aquí lo que se prueba es DÓNDE viaja `user_id`, porque el backend lo espera en
// un sitio distinto según el verbo: en el body del PUT y como query param del
// DELETE. Mandarlo en el lugar equivocado no da un error legible — el PUT
// respondería 422 y el DELETE también, pero el síntoma que se ve en pantalla es
// "no se pudo guardar" sin pista de por qué.

const MASCOTA_NUEVA: MascotaIn = {
  user_id: 4,
  rescatista_id: 4,
  nombre: 'Copito',
  especie: 'perro',
  sexo: 'macho',
  tamano: 'mediano',
  energia: 'media',
  edad_meses: 18,
  historia: 'Lo encontramos bajo un escombro y ya está sano.',
  zona: 'Armenia',
  telefono_contacto: '3001234567',
};

describe('crearMascota', () => {
  it('publica en POST /api/pets con el body tal cual', async () => {
    const fetchMock = espiarFetch({ id: 9 });

    await crearMascota(MASCOTA_NUEVA);

    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/pets');
    expect(initPedido(fetchMock).method).toBe('POST');
    expect(bodyEnviado(fetchMock)).toEqual(MASCOTA_NUEVA);
  });

  it('deja pasar report_id cuando la mascota viene de un reporte encontrado', async () => {
    const fetchMock = espiarFetch({ id: 9 });

    await crearMascota({ ...MASCOTA_NUEVA, report_id: 12 });

    expect(bodyEnviado(fetchMock).report_id).toBe(12);
  });
});

describe('editarMascota', () => {
  it('manda user_id EN EL BODY del PUT, no como query param', async () => {
    const fetchMock = espiarFetch({ id: 3 });

    await editarMascota(3, { user_id: 4, nombre: 'Copito', estado: 'en_proceso' });

    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/pets/3');
    expect(initPedido(fetchMock).method).toBe('PUT');
    expect(bodyEnviado(fetchMock)).toEqual({
      user_id: 4,
      nombre: 'Copito',
      estado: 'en_proceso',
    });
  });

  it('un 403 del backend se normaliza a ApiError con el detail en español', async () => {
    espiarFetchError(403, 'Solo quien publicó la mascota puede editarla');

    await expect(editarMascota(3, { user_id: 99 })).rejects.toThrow(ApiError);
    await expect(editarMascota(3, { user_id: 99 })).rejects.toThrow(
      'Solo quien publicó la mascota puede editarla',
    );
  });
});

describe('eliminarMascota', () => {
  it('manda user_id COMO QUERY PARAM del DELETE, no en el body', async () => {
    const fetchMock = espiarFetch204();

    await eliminarMascota(3, 7);

    const url = new URL(urlPedida(fetchMock));
    expect(url.pathname).toBe('/api/pets/3');
    expect(url.searchParams.get('user_id')).toBe('7');
    expect(initPedido(fetchMock).method).toBe('DELETE');
    expect(initPedido(fetchMock).body).toBeUndefined();
  });

  it('resuelve sin cuerpo con el 204 del backend', async () => {
    espiarFetch204();

    await expect(eliminarMascota(3, 7)).resolves.toBeUndefined();
  });

  it('un 403 del backend se normaliza a ApiError con el detail en español', async () => {
    espiarFetchError(403, 'Solo quien publicó la mascota puede despublicarla');

    await expect(eliminarMascota(3, 99)).rejects.toThrow(
      'Solo quien publicó la mascota puede despublicarla',
    );
  });
});

// ── Deck de descubrimiento (AD-03) ───────────────────────────────────────────

describe('registrarSwipe', () => {
  it('manda user_id, pet_id y direccion EN EL BODY, sin nada en la query', async () => {
    const fetchMock = espiarFetch({ id: 1 });

    await registrarSwipe(7, 3, 'like');

    // La URL va pelada a propósito: `SwipeIn` es un body, y mandar el adoptante
    // como query param daría un 422 sin pista útil para el usuario.
    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/swipes');
    expect(initPedido(fetchMock).method).toBe('POST');
    expect(bodyEnviado(fetchMock)).toEqual({ user_id: 7, pet_id: 3, direccion: 'like' });
  });

  it('"ahora no" viaja como pass, la otra mitad del contrato', async () => {
    const fetchMock = espiarFetch({ id: 2 });

    await registrarSwipe(7, 3, 'pass');

    expect(bodyEnviado(fetchMock).direccion).toBe('pass');
  });

  it('el 409 de una mascota ya adoptada llega como ApiError con el mensaje en español', async () => {
    espiarFetchError(409, 'Esta mascota ya encontró hogar');

    await expect(registrarSwipe(7, 3, 'like')).rejects.toThrow(ApiError);
    await expect(registrarSwipe(7, 3, 'like')).rejects.toThrow('Esta mascota ya encontró hogar');
  });
});

describe('listarDeck', () => {
  it('lleva al adoptante y repite los multivalor en vez de colapsarlos', async () => {
    const fetchMock = espiarFetch();

    await listarDeck(7, {
      especie: ['perro', 'gato'],
      edad: ['senior'],
      tamano: [],
      energia: [],
      zona: '',
    });

    const url = new URL(urlPedida(fetchMock));
    expect(url.pathname).toBe('/api/pets/deck');
    expect(url.searchParams.get('adoptante_id')).toBe('7');
    // `params.set` habría dejado especie=gato a secas: el deck parecería filtrar
    // a medias en vez de fallar de frente.
    expect(url.searchParams.getAll('especie')).toEqual(['perro', 'gato']);
    expect(url.searchParams.getAll('edad_categoria')).toEqual(['senior']);
    expect(url.search).toBe('?especie=perro&especie=gato&edad_categoria=senior&adoptante_id=7');
  });

  it('sin adoptante NO manda adoptante_id (visitante sin cuenta)', async () => {
    const fetchMock = espiarFetch();

    await listarDeck();

    // Mandar el `DEMO_USER_ID = 1` por defecto sería tratar a un visitante como
    // el usuario 1: el bug de autoría del fix `cc4de85`, ahora en el deck.
    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/pets/deck');
  });

  it('la zona solo viaja si se eligió una; vacía no deja la clave suelta', async () => {
    const conZona = espiarFetch();
    await listarDeck(7, { zona: 'Armenia' });
    expect(new URL(urlPedida(conZona)).searchParams.get('zona')).toBe('Armenia');

    const sinZona = espiarFetch();
    await listarDeck(7, { zona: '', especie: [], tamano: [], energia: [], edad: [] });
    expect(urlPedida(sinZona)).toBe('http://127.0.0.1:8000/api/pets/deck?adoptante_id=7');
  });
});

describe('las escrituras de adopción nunca mandan adoptante_id', () => {
  // `user_id` = quien publica; `adoptante_id` = quien mira. Colar el adoptante en
  // una escritura le daría permisos de autor sobre una mascota ajena: es el bug
  // de privacidad más probable del módulo, así que se asevera de frente.
  it('ni crearMascota, ni editarMascota, ni eliminarMascota, en la URL ni en el body', async () => {
    const alCrear = espiarFetch({ id: 9 });
    await crearMascota(MASCOTA_NUEVA);
    const alEditar = espiarFetch({ id: 3 });
    await editarMascota(3, { user_id: 4, nombre: 'Copito' });
    const alEliminar = espiarFetch204();
    await eliminarMascota(3, 7);

    for (const espia of [alCrear, alEditar, alEliminar]) {
      expect(urlPedida(espia)).not.toContain('adoptante_id');
      const body = initPedido(espia).body;
      if (body !== undefined) expect(String(body)).not.toContain('adoptante_id');
    }
  });
});

// ── Perfil de hogar (AD-04) ──────────────────────────────────────────────────
// El riesgo de estas dos funciones no es la URL sino **qué se hace con el 404**:
// "todavía no contestó el cuestionario" es el estado inicial de todo el mundo y
// no puede llegar a la pantalla como un error, pero tampoco puede tragarse el
// 403 ni un fallo de red.

const PERFIL_HOGAR: PerfilHogarIn = {
  user_id: 7,
  vivienda: 'apartamento',
  espacio_exterior: 'ninguno',
  personas_en_casa: 2,
  tiene_ninos: false,
  tiene_otros_perros: false,
  tiene_otros_gatos: false,
  horas_fuera_dia: 8,
  experiencia_previa: 'algo',
  presupuesto_mensual_cop: null,
  preferencia_especies: ['perro'],
  preferencia_tamanos: ['mediano'],
  preferencia_energia: 'media',
};

describe('guardarPerfilHogar', () => {
  it('hace PUT a la ruta del usuario con el cuestionario completo en el body', async () => {
    const espia = espiarFetch({ ...PERFIL_HOGAR });

    await guardarPerfilHogar(7, PERFIL_HOGAR);

    expect(urlPedida(espia)).toBe('http://127.0.0.1:8000/api/users/7/home-profile');
    const init = initPedido(espia);
    expect(init.method).toBe('PUT');
    expect(JSON.parse(String(init.body))).toEqual(PERFIL_HOGAR);
  });

  it('un 403 llega como ApiError con el detail en español, no como null', async () => {
    espiarFetchError(403, 'Solo puedes editar el perfil de hogar de tu cuenta');

    await expect(guardarPerfilHogar(7, PERFIL_HOGAR)).rejects.toThrow(
      'Solo puedes editar el perfil de hogar de tu cuenta',
    );
  });
});

describe('obtenerPerfilHogar', () => {
  it('pide la ruta con solicitante_id y devuelve el cuestionario', async () => {
    const espia = espiarFetch({ ...PERFIL_HOGAR });

    const perfil = await obtenerPerfilHogar(7, 7);

    expect(urlPedida(espia)).toBe(
      'http://127.0.0.1:8000/api/users/7/home-profile?solicitante_id=7',
    );
    expect(perfil?.vivienda).toBe('apartamento');
  });

  it('mapea el 404 a null: "todavía no contestó" no es un error', async () => {
    espiarFetchError(404, 'Todavía no completaste el cuestionario de tu hogar');

    await expect(obtenerPerfilHogar(7, 7)).resolves.toBeNull();
  });

  it('NO se traga el 403: mirar el hogar de otra persona sigue siendo un error', async () => {
    // Con un `.catch(() => null)` en la pantalla este caso devolvería `null` y el
    // wizard arrancaría en blanco sobre un perfil ajeno, sin decir nada.
    espiarFetchError(403, 'Solo puedes consultar tu propio perfil de hogar');

    await expect(obtenerPerfilHogar(7, 9)).rejects.toThrow(ApiError);
  });

  it('NO se traga un 500: un fallo real del servidor no es un perfil vacío', async () => {
    espiarFetchError(500, 'Internal Server Error');

    await expect(obtenerPerfilHogar(7, 7)).rejects.toThrow(ApiError);
  });
});

// ── Solicitudes de adopción (AD-05) ──────────────────────────────────────────
// Dos riesgos, y los dos son silenciosos:
//
// 1. **El filtro del listado.** `adoptante_id`, `organizacion_id` y
//    `publicador_id` son tres preguntas distintas ("las que envié", "las de mi
//    fundación", "las que recibí a título propio") y el backend responde 422 si
//    llegan cero o dos. Mandar el id correcto bajo la clave equivocada no da
//    error: devuelve las solicitudes de otra persona.
// 2. **La ruta de cada acción.** Las cuatro comparten forma de body
//    (`{user_id}`), así que confundir dos endpoints compila, responde 200 y
//    cambia el estado de una adopción real: `aprobar` en vez de `agendar-visita`
//    cierra la mascota y descarta a las demás familias.

describe('listarSolicitudes', () => {
  it('las que envió una persona van con adoptante_id, y solo con ese filtro', async () => {
    const espia = espiarFetch([]);

    await listarSolicitudes({ adoptanteId: 7 });

    expect(urlPedida(espia)).toBe('http://127.0.0.1:8000/api/solicitudes?adoptante_id=7');
  });

  it('las de una fundación van con organizacion_id', async () => {
    const espia = espiarFetch([]);

    await listarSolicitudes({ organizacionId: 2 });

    expect(urlPedida(espia)).toBe('http://127.0.0.1:8000/api/solicitudes?organizacion_id=2');
  });

  it('las que recibió quien publica a título propio van con publicador_id', async () => {
    const espia = espiarFetch([]);

    await listarSolicitudes({ publicadorId: 4 });

    expect(urlPedida(espia)).toBe('http://127.0.0.1:8000/api/solicitudes?publicador_id=4');
  });

  it('un 404 del backend llega como ApiError con el mensaje en español', async () => {
    espiarFetchError(404, 'La organización 99 no existe');

    await expect(listarSolicitudes({ organizacionId: 99 })).rejects.toThrow(ApiError);
    await expect(listarSolicitudes({ organizacionId: 99 })).rejects.toThrow(
      'La organización 99 no existe',
    );
  });
});

describe('obtenerSolicitud', () => {
  it('pide el detalle declarando quién pregunta (solicitante_id)', async () => {
    const espia = espiarFetch({ id: 5 });

    await obtenerSolicitud(5, 7);

    expect(urlPedida(espia)).toBe('http://127.0.0.1:8000/api/solicitudes/5?solicitante_id=7');
  });

  it('el 403 de una solicitud ajena llega como ApiError con el mensaje del backend', async () => {
    // El detalle lleva el cuestionario de hogar y el teléfono de quien adopta, y
    // los ids son adivinables: este error nunca puede degradarse a "vacío".
    espiarFetchError(403, 'Solo el adoptante o quien publicó la mascota pueden ver esta solicitud');

    await expect(obtenerSolicitud(5, 99)).rejects.toThrow(ApiError);
    await expect(obtenerSolicitud(5, 99)).rejects.toThrow(
      'Solo el adoptante o quien publicó la mascota pueden ver esta solicitud',
    );
  });
});

describe('las cuatro acciones sobre una solicitud', () => {
  it('agendarVisita pega a /agendar-visita con user_id en el body', async () => {
    const espia = espiarFetch({ id: 5, estado: 'visita_agendada' });

    await agendarVisita(5, 4);

    expect(urlPedida(espia)).toBe('http://127.0.0.1:8000/api/solicitudes/5/agendar-visita');
    expect(initPedido(espia).method).toBe('POST');
    expect(bodyEnviado(espia)).toEqual({ user_id: 4 });
  });

  it('pedirInformacion pega a /pedir-informacion con user_id en el body', async () => {
    const espia = espiarFetch({ id: 5, estado: 'en_revision' });

    await pedirInformacion(5, 4);

    expect(urlPedida(espia)).toBe('http://127.0.0.1:8000/api/solicitudes/5/pedir-informacion');
    expect(initPedido(espia).method).toBe('POST');
    expect(bodyEnviado(espia)).toEqual({ user_id: 4 });
  });

  it('aprobarSolicitud pega a /aprobar con user_id en el body', async () => {
    const espia = espiarFetch({ id: 5, estado: 'adoptado' });

    await aprobarSolicitud(5, 4);

    expect(urlPedida(espia)).toBe('http://127.0.0.1:8000/api/solicitudes/5/aprobar');
    expect(initPedido(espia).method).toBe('POST');
    expect(bodyEnviado(espia)).toEqual({ user_id: 4 });
  });

  it('descartarSolicitud manda el motivo junto al user_id: el backend lo exige', async () => {
    const espia = espiarFetch({ id: 5, estado: 'cerrado' });

    await descartarSolicitud(5, 4, 'Ya tenemos otra familia más cerca');

    expect(urlPedida(espia)).toBe('http://127.0.0.1:8000/api/solicitudes/5/descartar');
    expect(initPedido(espia).method).toBe('POST');
    expect(bodyEnviado(espia)).toEqual({
      user_id: 4,
      motivo: 'Ya tenemos otra familia más cerca',
    });
  });

  it('el 403 de quien no publicó la mascota llega con el mensaje del backend', async () => {
    // Las cuatro acciones son solo de quien publica: el adoptante recibe 403
    // igual que un desconocido (el match no es mutuo, ADR 0002).
    espiarFetchError(403, 'Solo quien publicó la mascota puede gestionar esta solicitud');

    await expect(aprobarSolicitud(5, 7)).rejects.toThrow(ApiError);
    await expect(aprobarSolicitud(5, 7)).rejects.toThrow(
      'Solo quien publicó la mascota puede gestionar esta solicitud',
    );
  });

  it('el 409 de una transición inválida llega tal cual, no como un error de red', async () => {
    // Es el error que de verdad va a ver quien publica (dos pestañas abiertas,
    // o un botón que quedó pintado sobre un estado viejo), y el texto del
    // backend es el que explica qué pasó.
    const MENSAJE =
      'Ya no puedes pedir más información: esta solicitud ya está cerrada. Actualiza la página para verla como está ahora.';
    espiarFetchError(409, MENSAJE);

    await expect(pedirInformacion(5, 4)).rejects.toThrow(ApiError);
    await expect(pedirInformacion(5, 4)).rejects.toThrow(MENSAJE);
  });
});

// ── Favoritos (AD-07) ────────────────────────────────────────────────────────
// Las tres rutas cuelgan de `/api/users/{userId}`, y aquí `userId` es **quien
// mira**, no quien publica (al revés que `Pet.user_id`). Lo que se prueba es
// dónde viaja cada dato: el `pet_id` en el body del POST y en la ruta del
// DELETE, y el `solicitante_id` requerido del GET — el backend responde 422 sin
// él y 403 si no coincide con el del path.

describe('marcarFavorita', () => {
  it('manda pet_id EN EL BODY del POST, con la persona en la ruta', async () => {
    const fetchMock = espiarFetch({ id: 3, es_favorito: true });

    await marcarFavorita(7, 3);

    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/users/7/favorites');
    expect(initPedido(fetchMock).method).toBe('POST');
    // `FavoritoIn` solo tiene `pet_id`: colar aquí un `user_id` sería mandar dos
    // fuentes del mismo actor, que es justo lo que el backend evitó no pidiéndolo.
    expect(bodyEnviado(fetchMock)).toEqual({ pet_id: 3 });
  });

  it('el 404 de una mascota que ya no existe llega como ApiError en español', async () => {
    espiarFetchError(404, 'La mascota 3 no existe');

    await expect(marcarFavorita(7, 3)).rejects.toThrow(ApiError);
    await expect(marcarFavorita(7, 3)).rejects.toThrow('La mascota 3 no existe');
  });
});

describe('desmarcarFavorita', () => {
  it('borra por ruta (/{userId}/favorites/{petId}) y sin cuerpo', async () => {
    const fetchMock = espiarFetch204();

    await desmarcarFavorita(7, 3);

    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/users/7/favorites/3');
    expect(initPedido(fetchMock).method).toBe('DELETE');
    // A diferencia de `eliminarMascota`, aquí no hay query param ninguno: el
    // actor y la mascota ya están los dos en la ruta.
    expect(initPedido(fetchMock).body).toBeUndefined();
  });

  it('resuelve sin cuerpo con el 204 del backend', async () => {
    espiarFetch204();

    await expect(desmarcarFavorita(7, 3)).resolves.toBeUndefined();
  });
});

describe('listarFavoritas', () => {
  it('manda solicitante_id con el MISMO id del path: es una auto-consulta', async () => {
    const fetchMock = espiarFetch();

    await listarFavoritas(7);

    // El param es requerido en el backend (sin él, 422) y cualquier otro valor da
    // 403: la lista de favoritos de alguien es su historial de navegación.
    expect(urlPedida(fetchMock)).toBe(
      'http://127.0.0.1:8000/api/users/7/favorites?solicitante_id=7',
    );
    expect(initPedido(fetchMock).method).toBeUndefined();
  });

  it('el 403 de una lista ajena llega con el mensaje del backend', async () => {
    espiarFetchError(403, 'Solo puedes ver las mascotas que guardaste en tu cuenta');

    await expect(listarFavoritas(7)).rejects.toThrow(
      'Solo puedes ver las mascotas que guardaste en tu cuenta',
    );
  });
});

// Candado del paso 4 de AD-07: el corazón del catálogo se pinta lleno con el
// `es_favorito` que trae el listado, y ese campo solo llega si el catálogo manda
// `adoptante_id`. Si alguien "limpia" ese parámetro del cliente, todos los
// corazones quedarían vacíos aunque la mascota estuviera guardada.
describe('listarMascotas sigue llevando al adoptante (lo que llena es_favorito)', () => {
  it('con adoptante manda adoptante_id', async () => {
    const fetchMock = espiarFetch();

    await listarMascotas({}, 7);

    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/pets?adoptante_id=7');
  });

  it('sin adoptante no lo inventa (el visitante anónimo no hereda favoritos ajenos)', async () => {
    const fetchMock = espiarFetch();

    await listarMascotas({});

    expect(urlPedida(fetchMock)).toBe('http://127.0.0.1:8000/api/pets');
  });
});
