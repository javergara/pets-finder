import {
  type Avistamiento,
  type AvistamientoIn,
  type CategoriaNecesidad,
  type Coincidencia,
  type Conteos,
  type Necesidad,
  type Organizacion,
  type OrganizacionIn,
  type Reporte,
  type ReporteIn,
  type ReunidosResumen,
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

export function obtenerConteos(): Promise<Conteos> {
  return request('/api/reports/conteos');
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
