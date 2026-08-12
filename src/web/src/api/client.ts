import { type UserProfile } from './types';

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
