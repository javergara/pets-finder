export interface Afinidad {
  score: number;
  explicacion: string;
  incompatible: boolean;
}

export interface Shelter {
  id: number;
  nombre: string;
  ciudad: string;
  verificado: boolean;
  adopciones_cerradas: number;
  tiempo_respuesta_horas: number;
  logo_url: string | null;
}

export interface Pet {
  id: number;
  shelter_id: number;
  nombre: string;
  especie: 'perro' | 'gato';
  raza: string;
  sexo: string;
  edad_meses: number;
  tamano: string;
  energia: string;
  fotos: string[];
  historia: string;
  tags: string[];
  esterilizado: boolean;
  vacunas_al_dia: boolean;
  microchip: boolean;
  desparasitado: boolean;
  apto_ninos: boolean;
  apto_perros: boolean;
  apto_gatos: boolean;
  estado: string;
  publicado_en: string;
  shelter: Shelter | null;
  afinidad: Afinidad | null;
  lat: number | null;
  lng: number | null;
  distancia_km: number | null;
}

export interface Match {
  id: number;
  user_id: number;
  pet_id: number;
  shelter_id: number;
  estado: string;
  creado_en: string;
}

export interface Swipe {
  id: number;
  user_id: number;
  pet_id: number;
  direccion: 'like' | 'pass';
  creado_en: string;
  match: Match | null;
}

export interface Filtros {
  especie: string[];
  tamano: string[];
  energia: string[];
  edadCategoria: string[];
  aptoNinos: boolean;
  aptoPerros: boolean;
  aptoGatos: boolean;
  distanciaKm: number;
}

export const FILTROS_DEFAULT: Filtros = {
  especie: [],
  tamano: [],
  energia: [],
  edadCategoria: [],
  aptoNinos: false,
  aptoPerros: false,
  aptoGatos: false,
  distanciaKm: 15,
};

export interface HomeProfile {
  vivienda: string;
  espacio_exterior: string;
  personas_en_casa: number;
  tiene_ninos: boolean;
  tiene_otros_perros: boolean;
  tiene_otros_gatos: boolean;
  horas_fuera_dia: number;
  experiencia_previa: string;
  presupuesto_mensual_cop: number;
  preferencia_especies: string[];
  preferencia_tamanos: string[];
  preferencia_energia: string;
}

export interface UserMetrics {
  matches_activos: number;
  visitas_agendadas: number;
  apadrinamientos: number;
}

export interface UserProfile {
  id: number;
  nombre: string;
  email: string;
  ciudad: string;
  barrio: string | null;
  avatar_url: string | null;
  bio: string | null;
  creado_en: string;
  home_profile: HomeProfile | null;
  metricas: UserMetrics | null;
}

export interface MatchWithPet {
  id: number;
  estado: string;
  creado_en: string;
  pet: {
    id: number;
    nombre: string;
    raza: string;
    edad_meses: number;
    fotos: string[];
    estado: string;
  };
  afinidad: Afinidad;
}

export interface ShelterMetrics {
  mascotas_publicadas: number;
  interesados_este_mes: number;
  visitas_agendadas: number;
  adopciones_cerradas: number;
  // Siempre 0 en el MVP: no existe tabla Sponsorship todavía (feature 12-sponsorship, backlog).
  apadrinamientos_recaudados_cop: number;
}

export interface ShelterProfile {
  id: number;
  nombre: string;
  ciudad: string;
  verificado: boolean;
  tiempo_respuesta_horas: number;
  logo_url: string | null;
  metricas: ShelterMetrics;
}

export interface SolicitanteResumen {
  id: number;
  nombre: string;
}

export interface SolicitudPetResumen {
  id: number;
  nombre: string;
  raza: string;
  fotos: string[];
}

export interface Solicitud {
  id: number; // id del Match, no un id de "solicitud" separado (no existe esa entidad).
  estado: string;
  creado_en: string;
  adoptante: SolicitanteResumen;
  pet: SolicitudPetResumen;
  afinidad: Afinidad;
  etiqueta: string;
}

export interface SolicitudDetalle extends Solicitud {
  bio: string | null;
  home_profile: HomeProfile;
}

export interface DescartarIn {
  motivo: string;
}

export interface PetIn {
  shelter_id: number;
  nombre: string;
  especie: string;
  raza: string;
  sexo: string;
  edad_meses: number;
  tamano: string;
  energia: string;
  historia: string;
  tags?: string[];
  esterilizado?: boolean;
  vacunas_al_dia?: boolean;
  microchip?: boolean;
  desparasitado?: boolean;
  apto_ninos?: boolean;
  apto_perros?: boolean;
  apto_gatos?: boolean;
  fotos?: string[];
}
