import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  ApiError,
  crearMascota,
  editarMascota,
  eliminarMascota,
  listarMascotas,
  mediaUrl,
  obtenerAdopcionesResumen,
  obtenerMascota,
} from './client';
import type { MascotaIn } from './types';

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
