import {
  type AdopcionesResumen,
  type Avistamiento,
  type AvisoAyuda,
  type AvisoAyudaIn,
  type AvistamientoIn,
  type CategoriaEdad,
  type CategoriaNecesidad,
  type Coincidencia,
  type ConsultaBusqueda,
  type ResultadoBusqueda,
  type Conteos,
  type DireccionSwipe,
  type EnergiaMascota,
  type EspecieAdopcion,
  type EstadoMascota,
  type Mascota,
  type MascotaIn,
  type MascotaUpdate,
  type Necesidad,
  type Organizacion,
  type PerfilHogar,
  type PerfilHogarIn,
  type OrganizacionIn,
  type Reporte,
  type ReporteIn,
  type ReunidosResumen,
  type Solicitud,
  type SolicitudDetalle,
  type Swipe,
  type TamanoMascota,
  type TipoOrganizacion,
  type UserProfile,
} from './types';

// En producción la API vive en el MISMO dominio (funciones serverless de Vercel,
// ADR 0007): base vacía = rutas relativas same-origin, sin CORS ni env vars.
// En dev (y en los tests de Vitest, donde DEV=true) apunta al uvicorn local.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '');

export class ApiError extends Error {}

// El arranque en frío del serverless puede tumbar el PRIMER request (visto en
// producción: /ayudar vacío con 28 organizaciones existiendo). Solo los GET se
// reintentan: son idempotentes; repetir un POST podría duplicar un reporte.
const REINTENTOS_GET = 2;
const ESPERA_MS = [600, 1800];

function esperar(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const metodo = (init?.method ?? 'GET').toUpperCase();
  const intentosMax = metodo === 'GET' ? REINTENTOS_GET + 1 : 1;

  let respuesta: Response | undefined;
  for (let intento = 0; intento < intentosMax; intento++) {
    if (intento > 0) await esperar(ESPERA_MS[intento - 1] ?? 1800);
    try {
      respuesta = await fetch(`${API_BASE_URL}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...init,
      });
    } catch (err) {
      // Fallo de red puro (cold start, DNS, offline): reintentar si quedan turnos.
      if (intento === intentosMax - 1) throw err;
      continue;
    }
    // 5xx transitorio en GET → reintentar; 4xx es del cliente y no se repite.
    if (respuesta.status >= 500 && intento < intentosMax - 1) continue;
    break;
  }
  if (!respuesta) throw new ApiError('Error de red');
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => ({}));
    throw new ApiError(cuerpo.detail ?? `Error de red (${respuesta.status})`);
  }
  // 204 No Content no trae body -- `.json()` sobre una respuesta vacía lanza
  // `SyntaxError: Unexpected end of JSON input`.
  if (respuesta.status === 204) {
    return undefined as T;
  }
  return respuesta.json() as Promise<T>;
}

export function mediaUrl(path: string): string {
  // Las fotos en Supabase Storage llegan como URL pública absoluta (ADR 0006);
  // las locales del seed/dev siguen siendo rutas relativas bajo /media.
  if (path.startsWith('http')) return path;
  return `${API_BASE_URL}${path}`;
}

export function obtenerPerfil(userId: number): Promise<UserProfile> {
  return request(`/api/users/${userId}`);
}

export function registrarUsuario(datos: {
  nombre: string;
  email: string;
  ciudad: string;
  barrio?: string;
}): Promise<UserProfile> {
  return request('/api/users', {
    method: 'POST',
    body: JSON.stringify(datos),
  });
}

export type FiltrosReportes = {
  tipo?: 'perdido' | 'encontrado';
  especie?: 'perro' | 'gato' | 'otro';
  zona?: string;
  raza?: string;
  color?: string;
  tamano?: 'pequeño' | 'mediano' | 'grande';
  userId?: number;
  estado?: 'activo' | 'reunido' | 'todos';
};

export function listarReportes(filtros: FiltrosReportes = {}): Promise<Reporte[]> {
  const params = new URLSearchParams();
  if (filtros.tipo) params.set('tipo', filtros.tipo);
  if (filtros.especie) params.set('especie', filtros.especie);
  if (filtros.zona) params.set('zona', filtros.zona);
  if (filtros.raza) params.set('raza', filtros.raza);
  if (filtros.color) params.set('color', filtros.color);
  if (filtros.tamano) params.set('tamano', filtros.tamano);
  if (filtros.userId !== undefined) params.set('user_id', String(filtros.userId));
  if (filtros.estado) params.set('estado', filtros.estado);
  const query = params.toString();
  return request(`/api/reports${query ? `?${query}` : ''}`);
}

export function buscarParecidos(consulta: ConsultaBusqueda): Promise<ResultadoBusqueda[]> {
  const params = new URLSearchParams({ tipo: consulta.tipo, especie: consulta.especie });
  if (consulta.zona) params.set('zona', consulta.zona);
  if (consulta.color) params.set('color', consulta.color);
  if (consulta.tamano) params.set('tamano', consulta.tamano);
  if (consulta.senas?.trim()) params.set('senas', consulta.senas.trim());
  return request(`/api/reports/busqueda?${params}`);
}

export function marcarReunido(reporteId: number, userId: number): Promise<Reporte> {
  return request(`/api/reports/${reporteId}/reunido`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
}

export function editarReporte(
  reporteId: number,
  datos: {
    user_id: number;
    nombre_mascota?: string;
    descripcion?: string;
    telefono_contacto?: string;
    foto_url?: string;
    barrio?: string;
    fecha_evento?: string;
    raza?: string;
    color?: string;
    tamano?: 'pequeño' | 'mediano' | 'grande';
    lat?: number;
    lng?: number;
  },
): Promise<Reporte> {
  return request(`/api/reports/${reporteId}`, {
    method: 'PUT',
    body: JSON.stringify(datos),
  });
}

export function eliminarReporte(reporteId: number, userId: number): Promise<void> {
  return request(`/api/reports/${reporteId}?user_id=${userId}`, { method: 'DELETE' });
}

export function obtenerReunidos(): Promise<ReunidosResumen> {
  return request('/api/reports/reunidos');
}

export function obtenerReporte(reporteId: number): Promise<Reporte> {
  return request(`/api/reports/${reporteId}`);
}

export function listarCoincidencias(reporteId: number): Promise<Coincidencia[]> {
  return request(`/api/reports/${reporteId}/coincidencias`);
}

export function crearReporte(datos: ReporteIn): Promise<Reporte> {
  return request('/api/reports', {
    method: 'POST',
    body: JSON.stringify(datos),
  });
}

/** Sube la foto de un reporte. No pasa por `request()`: con FormData el
 * navegador debe fijar solo el Content-Type multipart con su boundary — el
 * `Content-Type: application/json` que `request()` pone por defecto lo
 * rompería. */
export async function subirFoto(archivo: File): Promise<{ foto_url: string }> {
  const formData = new FormData();
  formData.append('foto', archivo);
  const respuesta = await fetch(`${API_BASE_URL}/api/uploads`, {
    method: 'POST',
    body: formData,
  });
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => ({}));
    throw new ApiError(cuerpo.detail ?? `Error de red (${respuesta.status})`);
  }
  return respuesta.json() as Promise<{ foto_url: string }>;
}

export function listarAvistamientos(reporteId: number): Promise<Avistamiento[]> {
  return request(`/api/reports/${reporteId}/avistamientos`);
}

export function crearAvistamiento(reporteId: number, datos: AvistamientoIn): Promise<Avistamiento> {
  return request(`/api/reports/${reporteId}/avistamientos`, {
    method: 'POST',
    body: JSON.stringify(datos),
  });
}

export function suscribirseANovedades(reporteId: number, email: string): Promise<unknown> {
  return request(`/api/reports/${reporteId}/suscripciones`, {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export function listarOrganizaciones(
  filtros: {
    tipo?: TipoOrganizacion;
    zona?: string;
  } = {},
): Promise<Organizacion[]> {
  const params = new URLSearchParams();
  if (filtros.tipo) params.set('tipo', filtros.tipo);
  if (filtros.zona) params.set('zona', filtros.zona);
  const query = params.toString();
  return request(`/api/organizaciones${query ? `?${query}` : ''}`);
}

export function obtenerOrganizacion(organizacionId: number): Promise<Organizacion> {
  return request(`/api/organizaciones/${organizacionId}`);
}

export function crearOrganizacion(datos: OrganizacionIn): Promise<Organizacion> {
  return request('/api/organizaciones', { method: 'POST', body: JSON.stringify(datos) });
}

export function editarOrganizacion(
  organizacionId: number,
  datos: { user_id: number } & Partial<Omit<OrganizacionIn, 'user_id'>> & {
      estado?: 'activo' | 'cerrado';
    },
): Promise<Organizacion> {
  return request(`/api/organizaciones/${organizacionId}`, {
    method: 'PUT',
    body: JSON.stringify(datos),
  });
}

export function eliminarOrganizacion(organizacionId: number, userId: number): Promise<void> {
  return request(`/api/organizaciones/${organizacionId}?user_id=${userId}`, { method: 'DELETE' });
}

export function listarNecesidades(organizacionId: number): Promise<Necesidad[]> {
  return request(`/api/organizaciones/${organizacionId}/necesidades`);
}

export function crearNecesidad(
  organizacionId: number,
  datos: { user_id: number; categoria: CategoriaNecesidad; descripcion: string },
): Promise<Necesidad> {
  return request(`/api/organizaciones/${organizacionId}/necesidades`, {
    method: 'POST',
    body: JSON.stringify(datos),
  });
}

export function cubrirNecesidad(
  organizacionId: number,
  necesidadId: number,
  userId: number,
): Promise<Necesidad> {
  return request(`/api/organizaciones/${organizacionId}/necesidades/${necesidadId}/cubierta`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
}

export function obtenerConteos(zona?: string): Promise<Conteos> {
  return request(`/api/reports/conteos${zona ? `?zona=${encodeURIComponent(zona)}` : ''}`);
}

/** Variante paginada del listado (feature 30): expone el total del header
 * X-Total-Count, que `request()` no puede leer. */
export async function listarReportesPaginado(
  filtros: FiltrosReportes & { q?: string } = {},
  limit = 12,
  offset = 0,
): Promise<{ items: Reporte[]; total: number }> {
  const params = new URLSearchParams();
  if (filtros.tipo) params.set('tipo', filtros.tipo);
  if (filtros.especie) params.set('especie', filtros.especie);
  if (filtros.zona) params.set('zona', filtros.zona);
  if (filtros.raza) params.set('raza', filtros.raza);
  if (filtros.color) params.set('color', filtros.color);
  if (filtros.tamano) params.set('tamano', filtros.tamano);
  if (filtros.estado) params.set('estado', filtros.estado);
  if (filtros.q) params.set('q', filtros.q);
  params.set('limit', String(limit));
  params.set('offset', String(offset));

  const respuesta = await fetch(`${API_BASE_URL}/api/reports?${params.toString()}`, {
    headers: { 'Content-Type': 'application/json' },
  });
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => ({}));
    throw new ApiError(cuerpo.detail ?? `Error de red (${respuesta.status})`);
  }
  const items = (await respuesta.json()) as Reporte[];
  const total = Number(respuesta.headers.get('X-Total-Count') ?? items.length);
  return { items, total };
}

export function listarAvisosAyuda(
  filtros: { tipo?: string; categoria?: string; zona?: string } = {},
): Promise<AvisoAyuda[]> {
  const params = new URLSearchParams();
  if (filtros.tipo) params.set('tipo', filtros.tipo);
  if (filtros.categoria) params.set('categoria', filtros.categoria);
  if (filtros.zona) params.set('zona', filtros.zona);
  const query = params.toString();
  return request(`/api/avisos-ayuda${query ? `?${query}` : ''}`);
}

export function crearAvisoAyuda(datos: AvisoAyudaIn): Promise<AvisoAyuda> {
  return request('/api/avisos-ayuda', { method: 'POST', body: JSON.stringify(datos) });
}

export function resolverAvisoAyuda(avisoId: number, userId: number): Promise<AvisoAyuda> {
  return request(`/api/avisos-ayuda/${avisoId}/resuelto`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
}

export function eliminarAvisoAyuda(avisoId: number, userId: number): Promise<void> {
  return request(`/api/avisos-ayuda/${avisoId}?user_id=${userId}`, { method: 'DELETE' });
}

// ── Adopción (AD-01) ─────────────────────────────────────────────────────────
// El catálogo filtra con **selección múltiple**: cada valor elegido viaja como
// un param repetido (`?especie=perro&especie=gato`). Eso obliga a `append` y
// prohíbe `set`, que pisa el valor anterior y deja la multi-selección reducida a
// uno solo — el filtro parecería funcionar a medias en vez de fallar de frente.
// Las etiquetas visibles y los defaults viven en `lib/adopcion.ts`.

export type FiltrosMascotas = {
  especie: EspecieAdopcion[];
  tamano: TamanoMascota[];
  energia: EnergiaMascota[];
  edad: CategoriaEdad[];
  /** '' = todas las zonas. */
  zona: string;
};

/** Catálogo de mascotas en adopción.
 *
 * ⚠️ `publicadaPorUserId` (→ `user_id`) es **quien publicó** la mascota, y
 * `adoptanteId` (→ `adoptante_id`) es **quien la está mirando**. Son parámetros
 * distintos y confundirlos es el bug de privacidad más fácil de cometer en este
 * módulo: filtrar "mis mascotas" por el adoptante devolvería las de otro. Por eso
 * ninguno de los dos se llama `userId` a secas.
 *
 * `adoptanteId` ya se manda aunque en AD-01 la respuesta no cambie: el backend lo
 * acepta desde ya y con AD-03/05/07 empezará a llenar `afinidad`, `es_favorito` y
 * `ya_solicitada` sin tocar este cliente.
 */
export function listarMascotas(
  filtros: Partial<FiltrosMascotas> & {
    estado?: EstadoMascota | 'todos';
    organizacionId?: number;
    publicadaPorUserId?: number;
  } = {},
  adoptanteId?: number,
): Promise<Mascota[]> {
  const params = new URLSearchParams();
  filtros.especie?.forEach((valor) => params.append('especie', valor));
  filtros.tamano?.forEach((valor) => params.append('tamano', valor));
  filtros.energia?.forEach((valor) => params.append('energia', valor));
  // El tramo de edad viaja con el nombre que ya usa el backend (`edad_categoria`,
  // `services/filtros.py`); el listado de AD-01 todavía no lo aplica en SQL.
  filtros.edad?.forEach((valor) => params.append('edad_categoria', valor));
  if (filtros.zona) params.set('zona', filtros.zona);
  if (filtros.estado) params.set('estado', filtros.estado);
  if (filtros.organizacionId !== undefined) {
    params.set('organizacion_id', String(filtros.organizacionId));
  }
  if (filtros.publicadaPorUserId !== undefined) {
    params.set('user_id', String(filtros.publicadaPorUserId));
  }
  if (adoptanteId !== undefined) params.set('adoptante_id', String(adoptanteId));
  const query = params.toString();
  return request(`/api/pets${query ? `?${query}` : ''}`);
}

export function obtenerMascota(mascotaId: number, adoptanteId?: number): Promise<Mascota> {
  const query = adoptanteId === undefined ? '' : `?adoptante_id=${adoptanteId}`;
  return request(`/api/pets/${mascotaId}${query}`);
}

/** Cuántas mascotas ya tienen hogar y las últimas seis: la métrica de esperanza
 * del catálogo, espejo de `obtenerReunidos()`. */
export function obtenerAdopcionesResumen(): Promise<AdopcionesResumen> {
  return request('/api/pets/adopciones');
}

// ── Escrituras de adopción (AD-02) ───────────────────────────────────────────
// ⚠️ `user_id` viaja en un sitio distinto según el verbo, y es la convención del
// repo, no un descuido: en el **body** del POST y el PUT, y como **query param**
// del DELETE (igual que `eliminarReporte` y `eliminarOrganizacion`). Cambiarlo de
// sitio da un 422 sin pista útil para el usuario.
//
// ⚠️ Ninguna de las tres manda `adoptante_id`. En este módulo `user_id` es quien
// publica y `adoptante_id` quien mira: mezclarlos le daría a un visitante
// permisos de autor sobre una mascota ajena.

/** Publica una mascota en adopción, a nombre de una organización o de un
 * rescatista (el XOR y el 403 de autoría los resuelve el backend). Con
 * `report_id` queda enlazada al reporte de "encontrada" del que salió. */
export function crearMascota(datos: MascotaIn): Promise<Mascota> {
  return request('/api/pets', {
    method: 'POST',
    body: JSON.stringify(datos),
  });
}

/** Edición parcial por quien publicó. `datos.user_id` es quien pide el cambio,
 * y va en el body (patrón de `editarReporte`/`editarOrganizacion`). */
export function editarMascota(mascotaId: number, datos: MascotaUpdate): Promise<Mascota> {
  return request(`/api/pets/${mascotaId}`, {
    method: 'PUT',
    body: JSON.stringify(datos),
  });
}

/** Despublica (borra) la mascota. Responde 204 sin cuerpo, que `request()` ya
 * sabe no parsear. `userId` va en la query: un DELETE no lleva body aquí. */
export function eliminarMascota(mascotaId: number, userId: number): Promise<void> {
  return request(`/api/pets/${mascotaId}?user_id=${userId}`, { method: 'DELETE' });
}

// ── Deck de descubrimiento (AD-03) ───────────────────────────────────────────
// Las dos funciones son del **adoptante**, no de quien publica: aquí `user_id`
// significa lo contrario que en las escrituras de arriba (`Swipe.user_id` es
// quien mira). Por eso el parámetro se llama `adoptanteId` en las dos.

/** Registra la decisión sobre una mascota del deck.
 *
 * El adoptante va **en el body** (`user_id`, como lo espera `SwipeIn`) y no en
 * la query: mandarlo como query param da un 422 sin pista útil para el usuario.
 *
 * Repetir el mismo swipe no es un error: el backend responde 200 con la misma
 * fila en vez de 409 (un doble-tap del gesto en móvil es un accidente del dedo).
 * `Swipe.solicitud` viaja siempre en `null` hasta AD-05.
 */
export function registrarSwipe(
  adoptanteId: number,
  mascotaId: number,
  direccion: DireccionSwipe,
): Promise<Swipe> {
  return request('/api/swipes', {
    method: 'POST',
    body: JSON.stringify({ user_id: adoptanteId, pet_id: mascotaId, direccion }),
  });
}

/** Las mascotas que le tocan a quien está descubriendo: solo disponibles, sin
 * las que ya swipeó, con su afinidad si tiene perfil de hogar.
 *
 * ⚠️ `adoptanteId` es **opcional y solo viaja si existe de verdad**. Sin cuenta
 * no se manda: `getActiveUserId()` cae al `DEMO_USER_ID = 1` y mandarlo haría
 * que un visitante viera el deck de otra persona —con sus swipes ya
 * descontados—, que es el bug de autoría del fix `cc4de85`. Sin él el backend
 * responde 200 igual, con `afinidad: null` y sin excluir nada.
 *
 * Multivalor con `append` (nunca `set`), por la misma razón que
 * `listarMascotas`: `set` pisa el valor anterior y deja la multi-selección
 * reducida a uno solo, así que el filtro parecería funcionar a medias.
 */
export function listarDeck(
  adoptanteId?: number,
  filtros: Partial<FiltrosMascotas> = {},
): Promise<Mascota[]> {
  const params = new URLSearchParams();
  filtros.especie?.forEach((valor) => params.append('especie', valor));
  filtros.tamano?.forEach((valor) => params.append('tamano', valor));
  filtros.energia?.forEach((valor) => params.append('energia', valor));
  filtros.edad?.forEach((valor) => params.append('edad_categoria', valor));
  // El deck acepta `zona` multivalor, pero en la UI sigue siendo de valor único
  // (mismo criterio que el resto de la app): '' = todas las zonas.
  if (filtros.zona) params.append('zona', filtros.zona);
  if (adoptanteId !== undefined) params.append('adoptante_id', String(adoptanteId));
  const query = params.toString();
  return request(`/api/pets/deck${query ? `?${query}` : ''}`);
}

/** Guarda (o reemplaza) el cuestionario de hogar. Upsert: siempre 200. */
export function guardarPerfilHogar(userId: number, datos: PerfilHogarIn): Promise<PerfilHogar> {
  return request(`/api/users/${userId}/home-profile`, {
    method: 'PUT',
    body: JSON.stringify(datos),
  });
}

/** El cuestionario propio, o `null` si esa persona todavía no lo contestó.
 *
 * ⚠️ **El 404 se mapea a `null`, y SOLO el 404.** "Todavía no contestó" no es un
 * error: es el estado inicial de todo el mundo, y la pantalla tiene que poder
 * distinguirlo de un fallo real. Por eso esta función no pasa por `request<T>()`
 * (que no expone el status y convierte cualquier respuesta no-ok en `ApiError`)
 * sino que hace su propio `fetch`, como `subirFoto` y `listarReportesPaginado`.
 *
 * ⚠️ Y por eso mismo está **prohibido** resolverlo con un `.catch(() => null)` en
 * la pantalla: eso se tragaría también el 403 (estar mirando el hogar de otra
 * persona) y los errores de red, y el wizard arrancaría en blanco pisando el
 * cuestionario que la persona ya había contestado.
 */
export async function obtenerPerfilHogar(
  userId: number,
  solicitanteId: number,
): Promise<PerfilHogar | null> {
  const respuesta = await fetch(
    `${API_BASE_URL}/api/users/${userId}/home-profile?solicitante_id=${solicitanteId}`,
    { headers: { 'Content-Type': 'application/json' } },
  );
  if (respuesta.status === 404) return null;
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => ({}));
    throw new ApiError(cuerpo.detail ?? `Error de red (${respuesta.status})`);
  }
  return respuesta.json() as Promise<PerfilHogar>;
}

// ── Solicitudes de adopción (AD-05) ──────────────────────────────────────────
// Aquí conviven las dos mitades del módulo: quien adopta solo lee (`las que
// envié`), y quien publica lee y además mueve el estado con las cuatro
// acciones. El corte no lo hace este archivo — lo hace el backend con un 403 —,
// pero sí lo refleja: `listarSolicitudes` y `obtenerSolicitud` las usan los dos;
// las cuatro acciones, solo quien publicó la mascota.

/** El filtro de `GET /api/solicitudes`: **exactamente uno de los tres**.
 *
 * Son tres preguntas distintas ("las que envié", "las de mi fundación", "las que
 * recibí a título propio") y el backend responde 422 si llegan cero o dos —un
 * guard escrito a mano, porque FastAPI sabe exigir un parámetro requerido pero
 * no "uno de tres"—. La unión hace ese mismo trabajo en tiempo de compilación,
 * así que ese 422 es inalcanzable desde la app.
 *
 * ⚠️ Los `?: never` no son ruido: **medido en este repo**, una unión pelada
 * (`{adoptanteId} | {organizacionId} | {publicadorId}`) acepta
 * `{ adoptanteId: 7, organizacionId: 2 }` sin protestar. TypeScript solo aplica
 * el chequeo de propiedades de más contra la unión entera, así que la clave
 * sobrante se considera legítima porque existe en otro miembro. Con los `never`
 * declarados, ese literal no compila. */
export type FiltroSolicitudes =
  | { adoptanteId: number; organizacionId?: never; publicadorId?: never }
  | { organizacionId: number; adoptanteId?: never; publicadorId?: never }
  | { publicadorId: number; adoptanteId?: never; organizacionId?: never };

/** Las solicitudes de una persona (las que envió) o de quien publica (las que
 * recibió), lo más reciente primero.
 *
 * `acciones_disponibles` viene calculado por el backend para quien pregunta: al
 * adoptante le llega siempre `[]`.
 */
export function listarSolicitudes(filtro: FiltroSolicitudes): Promise<Solicitud[]> {
  const params = new URLSearchParams();
  // Tres `if` independientes en vez de una cadena con `else`: el tipo ya
  // garantiza que solo uno llega definido, y así esta función nunca elige por su
  // cuenta cuál filtro gana si alguna vez la llamaran desde JavaScript sin
  // tipos — el backend respondería su 422, que es la respuesta honesta.
  if (filtro.adoptanteId !== undefined) params.set('adoptante_id', String(filtro.adoptanteId));
  if (filtro.organizacionId !== undefined) {
    params.set('organizacion_id', String(filtro.organizacionId));
  }
  if (filtro.publicadorId !== undefined) params.set('publicador_id', String(filtro.publicadorId));
  return request(`/api/solicitudes?${params}`);
}

/** El detalle: el cuestionario del hogar, el mensaje y el teléfono de quien
 * adopta.
 *
 * `solicitanteId` es requerido y solo lo pasan dos personas: quien envió la
 * solicitud y quien publicó la mascota. Cualquier otra recibe **403** — los ids
 * son secuenciales y adivinables, así que sin ese corte cualquiera leería datos
 * personales ajenos. */
export function obtenerSolicitud(
  solicitudId: number,
  solicitanteId: number,
): Promise<SolicitudDetalle> {
  return request(`/api/solicitudes/${solicitudId}?solicitante_id=${solicitanteId}`);
}

// Las cuatro acciones de quien publicó la mascota. Una función por endpoint, con
// su nombre y su ruta escritos enteros, en vez de un `avanzarSolicitud(accion)`
// genérico: cada una cambia el estado de una adopción real (`aprobar` cierra la
// mascota y descarta a las demás familias), y con un parámetro suelto ese
// destino se decidiría en una variable que ningún tipo mira dos veces.
//
// Las cuatro devuelven el detalle ya actualizado —incluida
// `acciones_disponibles` recalculada—, así que la pantalla no necesita un `GET`
// detrás de cada botón. Un 403 significa que quien pide no es el publicador; un
// 409, que esa acción no es válida desde el estado actual (una pestaña vieja,
// típicamente): los dos llegan como `ApiError` con el texto del backend, que ya
// es copy de producto en español.

/** Cita para conocer a la mascota. Válida desde `solicitado` o `en_revision`. */
export function agendarVisita(solicitudId: number, userId: number): Promise<SolicitudDetalle> {
  return request(`/api/solicitudes/${solicitudId}/agendar-visita`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
}

/** Deja la solicitud `en_revision`. Válida **solo** desde `solicitado`: pedirla
 * dos veces es 409, no un no-op. */
export function pedirInformacion(solicitudId: number, userId: number): Promise<SolicitudDetalle> {
  return request(`/api/solicitudes/${solicitudId}/pedir-informacion`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
}

/** Cierra la adopción: esta solicitud gana, la mascota sube a la franja de
 * celebración y **las demás de esa mascota se cierran solas**. Es irreversible.
 */
export function aprobarSolicitud(solicitudId: number, userId: number): Promise<SolicitudDetalle> {
  return request(`/api/solicitudes/${solicitudId}/aprobar`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
}

/** Cierra la solicitud con un motivo **obligatorio** (el backend responde 422 si
 * llega vacío o en blanco).
 *
 * ⚠️ Ese motivo es la nota interna de quien publica: se guarda, pero no vuelve
 * en ninguna respuesta y el adoptante nunca lo ve (ADR 0002). Por eso no existe
 * en ningún tipo de `api/types.ts`. */
export function descartarSolicitud(
  solicitudId: number,
  userId: number,
  motivo: string,
): Promise<SolicitudDetalle> {
  return request(`/api/solicitudes/${solicitudId}/descartar`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, motivo }),
  });
}

// ── Favoritos (AD-07) ────────────────────────────────────────────────────────
// Las tres cuelgan de `/api/users/{userId}` y aquí `userId` es **quien mira**,
// exactamente al revés que `Pet.user_id` (quien publica). Las dos son ids de
// `users`, así que nada avisa si se cruzan: el síntoma sería que a una fundación
// le salgan sus propias mascotas como "guardadas".
//
// ⚠️ **Ninguna se llama sin cuenta.** `getActiveUserId()` cae al
// `DEMO_USER_ID = 1`, que en producción es una persona real: guardar sin cuenta
// escribiría en la lista de otra, y leer sin cuenta mostraría la suya. El gate
// (`hasActiveUser()` → `/registro?volver=…`) vive en cada pantalla que las usa,
// como el de "Me interesa" del deck.
//
// Una función por endpoint, con su verbo escrito entero, en vez de un
// `alternarFavorita(guardada)` con un booleano: el destino de la escritura no se
// decide en una variable que ningún tipo mira dos veces.

/** Guarda la mascota en la lista de quien mira.
 *
 * `pet_id` viaja **en el body** (`FavoritoIn`), no en la query: el actor ya está
 * en la ruta. Repetirlo no es error —el backend responde 200 con la misma fila
 * en vez de 409, porque el doble-tap de un corazón es un accidente del dedo— y
 * la respuesta es la mascota completa ya con `es_favorito: true`, así que la
 * tarjeta no necesita volver a pedirla. */
export function marcarFavorita(userId: number, petId: number): Promise<Mascota> {
  return request(`/api/users/${userId}/favorites`, {
    method: 'POST',
    body: JSON.stringify({ pet_id: petId }),
  });
}

/** Quita la mascota de la lista. Responde **204 siempre**, incluso si no estaba
 * guardada: apagar dos veces el corazón no es un error que haya que pintar. */
export function desmarcarFavorita(userId: number, petId: number): Promise<void> {
  return request(`/api/users/${userId}/favorites/${petId}`, { method: 'DELETE' });
}

/** Las mascotas guardadas por esa persona, lo último guardado primero.
 *
 * ⚠️ `solicitante_id` es **requerido** por el backend (sin él, 422) y viaja con
 * el mismo id del path porque esto es siempre una auto-consulta: una lista de
 * favoritos es un historial de navegación, y pedir la de otra persona responde
 * 403. Que sea el mismo valor dos veces no es redundancia inútil — es lo que
 * convierte una fuga accidental (el frontend cayendo al `DEMO_USER_ID`) en algo
 * que solo puede pasar a propósito. */
export function listarFavoritas(userId: number): Promise<Mascota[]> {
  return request(`/api/users/${userId}/favorites?solicitante_id=${userId}`);
}
