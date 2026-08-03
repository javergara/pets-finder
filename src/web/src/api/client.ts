import { FILTROS_DEFAULT, type Filtros, type MatchWithPet, type Pet, type Swipe } from './types';

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

export function listarMascotas(userId: number, filtros?: Filtros): Promise<Pet[]> {
  const params = new URLSearchParams();
  params.set('user_id', String(userId));
  filtros?.especie.forEach((valor) => params.append('especie', valor));
  filtros?.tamano.forEach((valor) => params.append('tamano', valor));
  filtros?.energia.forEach((valor) => params.append('energia', valor));
  filtros?.edadCategoria.forEach((valor) => params.append('edad_categoria', valor));
  if (filtros?.aptoNinos) params.set('apto_ninos', 'true');
  if (filtros?.aptoPerros) params.set('apto_perros', 'true');
  if (filtros?.aptoGatos) params.set('apto_gatos', 'true');
  params.set('distancia_km', String(filtros?.distanciaKm ?? FILTROS_DEFAULT.distanciaKm));
  return request(`/api/pets?${params.toString()}`);
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
