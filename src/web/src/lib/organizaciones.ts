import type { TipoOrganizacion } from '../api/types';

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
};

export const TIPOS_ORGANIZACION = Object.keys(ETIQUETA_TIPO_ORGANIZACION) as TipoOrganizacion[];
