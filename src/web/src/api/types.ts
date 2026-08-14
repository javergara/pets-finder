// Procedencia de un reporte creado por el crawler de redes (ADR 0010). Un post
// con varias mascotas produce varios reportes que comparten url_post y se
// distinguen por indice_mascota. Unión discriminada por `plataforma` (espejo
// del schema de la API): cada plataforma aporta sus campos propios sobre la
// base común. Se llama plataforma y no "red" porque no todo origen es una red
// social (WhatsApp es mensajería).
type CrawlMetadataBase = {
  url_post: string | null;
  autor_handle: string | null;
  fecha_post: string | null;
  texto_original: string | null;
  modelo_extraccion: string | null;
  confianza: number | null;
  indice_mascota: number;
  total_mascotas: number;
};

export type CrawlMetadata =
  | (CrawlMetadataBase & { plataforma: 'instagram' | 'x' | 'tiktok' | 'desconocida' })
  | (CrawlMetadataBase & { plataforma: 'facebook'; grupo?: string | null })
  | (CrawlMetadataBase & { plataforma: 'whatsapp'; nombre_grupo?: string | null });

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
  // Todas las fotos, la principal primero (feature 41). Opcional para no
  // obligar a cada fixture: la UI cae a foto_url si falta.
  fotos?: string[];
  zona: string;
  ciudad_texto: string | null;
  barrio: string | null;
  lat: number;
  lng: number;
  situacion: 'conmigo' | 'vista' | null;
  fecha_evento: string;
  // Null solo en reportes con fuente 'crawl': el contacto es el post original.
  telefono_contacto: string | null;
  // Canales opcionales de contacto (feature 40).
  instagram: string | null;
  facebook: string | null;
  fuente: 'manual' | 'crawl';
  crawl_metadata: CrawlMetadata | null;
  idempotency_id: string | null;
  estado: 'activo' | 'reunido';
  creado_en: string;
  resuelto_en: string | null;
};

export type Coincidencia = Reporte & { distancia_km: number; razones: string[] };

export type ResultadoBusqueda = Reporte & { parecido: number; razones: string[] };

export type ConsultaBusqueda = {
  tipo: 'perdido' | 'encontrado';
  especie: 'perro' | 'gato' | 'otro';
  zona?: string;
  color?: string;
  tamano?: string;
  senas?: string;
};

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
  fotos_extra?: string[];
  zona: string;
  ciudad_texto?: string;
  barrio?: string;
  lat: number;
  lng: number;
  situacion?: 'conmigo' | 'vista';
  fecha_evento: string;
  telefono_contacto: string;
  instagram?: string;
  facebook?: string;
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

export type Conteos = {
  perdidos: number;
  encontrados: number;
};

export type TipoAvisoAyuda = 'pido' | 'ofrezco';

export type CategoriaAvisoAyuda =
  | 'hogar_de_paso'
  | 'transporte'
  | 'alimento'
  | 'salud'
  | 'rescate'
  | 'otro';

export type AvisoAyuda = {
  id: number;
  user_id: number;
  tipo: TipoAvisoAyuda;
  categoria: CategoriaAvisoAyuda;
  titulo: string;
  descripcion: string;
  zona: string;
  ciudad_texto: string | null;
  barrio: string | null;
  telefono_contacto: string;
  estado: 'activo' | 'resuelto';
  creado_en: string;
  resuelto_en: string | null;
};

export type AvisoAyudaIn = {
  user_id: number;
  tipo: TipoAvisoAyuda;
  categoria: CategoriaAvisoAyuda;
  titulo: string;
  descripcion: string;
  zona: string;
  ciudad_texto?: string;
  barrio?: string;
  telefono_contacto: string;
};
