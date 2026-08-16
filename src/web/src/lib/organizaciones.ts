import type { CategoriaNecesidad, TipoOrganizacion } from '../api/types';

// Catálogo de tipos de la red de apoyo (feature 32): etiqueta visible + color
// del badge/pin (tokens del design system; MapaLienzo conoce estos hex).
export const ETIQUETA_TIPO_ORGANIZACION: Record<
  TipoOrganizacion,
  { texto: string; color: string }
> = {
  centro_acopio: { texto: 'Centro de acopio', color: 'bg-ochre' },
  fundacion: { texto: 'Fundación', color: 'bg-forest' },
  tienda: { texto: 'Tienda de mascotas', color: 'bg-ink' },
  veterinaria: { texto: 'Veterinaria', color: 'bg-danger' },
  // Entrenadores caninos (feature 47): vitrina + apoyo, contacto por WhatsApp.
  entrenador: { texto: 'Entrenador', color: 'bg-forest-hover' },
};

export const TIPOS_ORGANIZACION = Object.keys(ETIQUETA_TIPO_ORGANIZACION) as TipoOrganizacion[];

// Categorías de necesidades (feature 33).
export const ETIQUETA_CATEGORIA_NECESIDAD: Record<CategoriaNecesidad, string> = {
  alimento: 'Alimento',
  medicinas: 'Medicinas',
  insumos: 'Insumos',
  voluntarios: 'Voluntarios',
  hogar_de_paso: 'Hogar de paso',
  dinero: 'Dinero',
  otro: 'Otro',
};

export const CATEGORIAS_NECESIDAD = Object.keys(
  ETIQUETA_CATEGORIA_NECESIDAD,
) as CategoriaNecesidad[];
