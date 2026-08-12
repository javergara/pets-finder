export type Reporte = {
  id: number;
  user_id: number;
  tipo: 'perdido' | 'encontrado';
  especie: 'perro' | 'gato' | 'otro';
  nombre_mascota: string | null;
  raza: string | null;
  color: string | null;
  tamano: 'pequeño' | 'mediano' | 'grande' | null;
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

export type ReunidosResumen = {
  total: number;
  recientes: Reporte[];
};

export type ReporteIn = {
  user_id: number;
  tipo: 'perdido' | 'encontrado';
  especie: 'perro' | 'gato' | 'otro';
  nombre_mascota?: string;
  raza?: string;
  color?: string;
  tamano?: 'pequeño' | 'mediano' | 'grande';
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

export type Avistamiento = {
  id: number;
  report_id: number;
  lat: number;
  lng: number;
  fecha: string;
  comentario: string;
  nombre: string | null;
  creado_en: string;
};

export type AvistamientoIn = {
  lat: number;
  lng: number;
  fecha: string;
  comentario: string;
  nombre?: string;
};

export type TipoOrganizacion = 'centro_acopio' | 'fundacion' | 'tienda' | 'veterinaria';

export type Organizacion = {
  id: number;
  user_id: number;
  tipo: TipoOrganizacion;
  nombre: string;
  descripcion: string;
  zona: string;
  ciudad_texto: string | null;
  barrio: string | null;
  direccion: string;
  lat: number;
  lng: number;
  telefono_contacto: string;
  horario: string | null;
  como_donar: string | null;
  foto_url: string | null;
  estado: 'activo' | 'cerrado';
  creado_en: string;
  // Contador calculado por el backend (feature 33).
  necesidades_pendientes: number;
};

export type OrganizacionIn = {
  user_id: number;
  tipo: TipoOrganizacion;
  nombre: string;
  descripcion: string;
  zona: string;
  ciudad_texto?: string;
  barrio?: string;
  direccion: string;
  lat: number;
  lng: number;
  telefono_contacto: string;
  horario?: string;
  como_donar?: string;
  foto_url?: string;
};

export type CategoriaNecesidad =
  | 'alimento'
  | 'medicinas'
  | 'insumos'
  | 'voluntarios'
  | 'hogar_de_paso'
  | 'dinero'
  | 'otro';

export type Necesidad = {
  id: number;
  organizacion_id: number;
  categoria: CategoriaNecesidad;
  descripcion: string;
  estado: 'pendiente' | 'cubierta';
  creado_en: string;
  cubierta_en: string | null;
};
