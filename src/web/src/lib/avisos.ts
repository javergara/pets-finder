import type { CategoriaAvisoAyuda, TipoAvisoAyuda } from '../api/types';

// Catálogos del tablero de ayuda entre personas (feature 42).
export const TIPOS_AVISO: readonly TipoAvisoAyuda[] = ['pido', 'ofrezco'];

export const ETIQUETA_TIPO_AVISO: Record<TipoAvisoAyuda, { texto: string; color: string }> = {
  pido: { texto: 'Necesita ayuda', color: 'bg-danger' },
  ofrezco: { texto: 'Ofrece ayuda', color: 'bg-forest' },
};

export const CATEGORIAS_AVISO: readonly CategoriaAvisoAyuda[] = [
  'hogar_de_paso',
  'transporte',
  'alimento',
  'salud',
  'rescate',
  'otro',
];

export const ETIQUETA_CATEGORIA_AVISO: Record<CategoriaAvisoAyuda, string> = {
  hogar_de_paso: 'Hogar de paso',
  transporte: 'Transporte',
  alimento: 'Alimento',
  salud: 'Salud / veterinaria',
  rescate: 'Rescate',
  otro: 'Otro',
};
