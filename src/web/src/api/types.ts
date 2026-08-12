export type Reporte = {
  id: number;
  user_id: number;
  tipo: 'perdido' | 'encontrado';
  especie: 'perro' | 'gato' | 'otro';
  nombre_mascota: string | null;
  descripcion: string;
  foto_url: string | null;
  zona: string;
  ciudad_texto: string | null;
  barrio: string | null;
  lat: number;
  lng: number;
  situacion: 'conmigo' | 'vista' | null;
  fecha_evento: string;
  telefono_contacto: string;
  estado: 'activo' | 'reunido';
  creado_en: string;
  resuelto_en: string | null;
};

export type Coincidencia = Reporte & { distancia_km: number };

export type ReporteIn = {
  user_id: number;
  tipo: 'perdido' | 'encontrado';
  especie: 'perro' | 'gato' | 'otro';
  nombre_mascota?: string;
  descripcion: string;
  foto_url?: string;
  zona: string;
  ciudad_texto?: string;
  barrio?: string;
  lat: number;
  lng: number;
  situacion?: 'conmigo' | 'vista';
  fecha_evento: string;
  telefono_contacto: string;
};

export type UserProfile = {
  id: number;
  nombre: string;
  email: string;
  ciudad: string;
  barrio: string | null;
  lat: number | null;
  lng: number | null;
  avatar_url: string | null;
  bio: string | null;
  creado_en: string;
};
