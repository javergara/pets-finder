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
  type EnergiaMascota,
  type EspecieAdopcion,
  type EstadoMascota,
  type Mascota,
  type MascotaIn,
  type MascotaUpdate,
  type Necesidad,
  type Organizacion,
  type OrganizacionIn,
  type Reporte,
  type ReporteIn,
  type ReunidosResumen,
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const respuesta = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
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
