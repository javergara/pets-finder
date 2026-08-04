import {
  FILTROS_DEFAULT,
  type Filtros,
  type HomeProfile,
  type MascotaNecesitaApoyo,
  type MatchWithPet,
  type Pet,
  type PetIn,
  type ShelterProfile,
  type Solicitud,
  type SolicitudDetalle,
  type Sponsorship,
  type SponsorshipIn,
  type Swipe,
  type ThreadConMensajes,
  type UserProfile,
} from './types';

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

export function obtenerThread(matchId: number): Promise<ThreadConMensajes> {
  return request(`/api/matches/${matchId}/thread`);
}

/** Deriva la URL del WebSocket del hilo a partir del mismo `API_BASE_URL`
 * que ya usa `mediaUrl`, reemplazando el esquema `http`/`https` por
 * `ws`/`wss`. Identidad por query param (`user_id` para el adoptante,
 * `shelter_id` para el refugio) -- ver `routers/chat.py`. */
export function chatSocketUrl(
  matchId: number,
  rol: 'adoptante' | 'refugio',
  participantId: number,
): string {
  const wsBase = API_BASE_URL.replace(/^http/, 'ws');
  const paramNombre = rol === 'adoptante' ? 'user_id' : 'shelter_id';
  return `${wsBase}/ws/matches/${matchId}/thread?rol=${rol}&${paramNombre}=${participantId}`;
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

export function guardarHomeProfile(userId: number, home: HomeProfile): Promise<HomeProfile> {
  return request(`/api/users/${userId}/home-profile`, {
    method: 'PUT',
    body: JSON.stringify(home),
  });
}

export function obtenerRefugio(shelterId: number): Promise<ShelterProfile> {
  return request(`/api/shelters/${shelterId}`);
}

export function listarSolicitudes(shelterId: number): Promise<Solicitud[]> {
  return request(`/api/shelters/${shelterId}/solicitudes`);
}

export function obtenerSolicitud(shelterId: number, matchId: number): Promise<SolicitudDetalle> {
  return request(`/api/shelters/${shelterId}/solicitudes/${matchId}`);
}

export function publicarMascota(payload: PetIn): Promise<Pet> {
  return request('/api/pets', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function agendarVisita(shelterId: number, matchId: number): Promise<SolicitudDetalle> {
  return request(`/api/shelters/${shelterId}/solicitudes/${matchId}/agendar-visita`, {
    method: 'POST',
  });
}

export function pedirInformacion(shelterId: number, matchId: number): Promise<SolicitudDetalle> {
  return request(`/api/shelters/${shelterId}/solicitudes/${matchId}/pedir-informacion`, {
    method: 'POST',
  });
}

export function descartarSolicitud(
  shelterId: number,
  matchId: number,
  motivo: string,
): Promise<SolicitudDetalle> {
  return request(`/api/shelters/${shelterId}/solicitudes/${matchId}/descartar`, {
    method: 'POST',
    body: JSON.stringify({ motivo }),
  });
}

export function listarNecesitanApoyo(): Promise<MascotaNecesitaApoyo[]> {
  return request('/api/pets/necesitan-apoyo');
}

export function crearApadrinamiento(payload: SponsorshipIn): Promise<Sponsorship> {
  return request('/api/sponsorships', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function listarApadrinamientos(userId: number): Promise<Sponsorship[]> {
  return request(`/api/users/${userId}/sponsorships`);
}
