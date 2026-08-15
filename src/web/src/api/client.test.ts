import { afterEach, describe, expect, it, vi } from 'vitest';
import { listarMascotas, mediaUrl, obtenerAdopcionesResumen, obtenerMascota } from './client';

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

function urlPedida(fetchMock: ReturnType<typeof espiarFetch>): string {
  return String(fetchMock.mock.calls[0][0]);
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
