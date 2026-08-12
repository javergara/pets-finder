import { type Reporte, type ReporteIn, type UserProfile } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

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
  estado?: 'activo' | 'reunido' | 'todos';
};

export function listarReportes(filtros: FiltrosReportes = {}): Promise<Reporte[]> {
  const params = new URLSearchParams();
  if (filtros.tipo) params.set('tipo', filtros.tipo);
  if (filtros.especie) params.set('especie', filtros.especie);
  if (filtros.zona) params.set('zona', filtros.zona);
  if (filtros.estado) params.set('estado', filtros.estado);
  const query = params.toString();
  return request(`/api/reports${query ? `?${query}` : ''}`);
}

export function obtenerReporte(reporteId: number): Promise<Reporte> {
  return request(`/api/reports/${reporteId}`);
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
