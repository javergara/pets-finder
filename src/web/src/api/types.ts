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
