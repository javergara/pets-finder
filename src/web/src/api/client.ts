import type { MatchWithPet, Pet, Swipe } from './types';

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
  return respuesta.json() as Promise<T>;
}

export function mediaUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export function listarMascotas(userId: number): Promise<Pet[]> {
  return request(`/api/pets?user_id=${userId}`);
}

export function obtenerMascota(petId: number, userId: number): Promise<Pet> {
  return request(`/api/pets/${petId}?user_id=${userId}`);
}

export function registrarSwipe(
  userId: number,
  petId: number,
  direccion: 'like' | 'pass',
): Promise<Swipe> {
  return request('/api/swipes', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, pet_id: petId, direccion }),
  });
}

export function listarMatches(userId: number): Promise<MatchWithPet[]> {
  return request(`/api/matches?user_id=${userId}`);
}
