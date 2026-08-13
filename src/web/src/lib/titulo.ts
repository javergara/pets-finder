import type { Reporte } from '../api/types';

const ETIQUETA_ESPECIE = { perro: 'Perro', gato: 'Gato', otro: 'Otro animal' } as const;

type AtributosTitulo = Pick<Reporte, 'nombre_mascota' | 'especie' | 'tamano' | 'color'>;

/** Título reconocible para un reporte: el nombre si lo tiene; si no, una
 * composición con los atributos presentes — "Perro mediano café" dice mucho
 * más que "Perro" en una tarjeta (benchmark encontradogs, product-research §9).
 * El color "Otro" no aporta señas, así que no se incluye. */
export function tituloReporte(reporte: AtributosTitulo): string {
  if (reporte.nombre_mascota) return reporte.nombre_mascota;

  const partes = [
    ETIQUETA_ESPECIE[reporte.especie],
    reporte.tamano,
    reporte.color && reporte.color !== 'Otro' ? reporte.color.toLowerCase() : null,
  ];
  return partes.filter(Boolean).join(' ');
}
