import type { FiltrosMascotas } from '../api/client';
import type {
  CategoriaEdad,
  EnergiaMascota,
  EspecieAdopcion,
  EstadoMascota,
  Mascota,
  SexoMascota,
  TamanoMascota,
} from '../api/types';

// Catálogos de copy y funciones puras del módulo de adopción (AD-01).
// `api/types.ts` es un espejo de los schemas y no exporta valores: las etiquetas
// visibles y los cálculos viven aquí, sin estado de UI y sin tocar la red.
//
// Ojo con el dominio: `Mascota` es adopción (tabla `pets`); los perdidos y
// encontrados son `Reporte` y tienen sus propias etiquetas en `lib/titulo.ts` y
// en `ReporteCard`. El repo duplica etiquetas a propósito entre dominios (ya
// pasa con `ETIQUETA_ESPECIE`) y comparte solo la lógica.

export const ETIQUETA_ESPECIE_ADOPCION: Record<EspecieAdopcion, string> = {
  perro: 'Perro',
  gato: 'Gato',
  otro: 'Otro animal',
};

export const ESPECIES_ADOPCION = Object.keys(ETIQUETA_ESPECIE_ADOPCION) as EspecieAdopcion[];

export const ETIQUETA_SEXO: Record<SexoMascota, string> = {
  macho: 'Macho',
  hembra: 'Hembra',
};

export const SEXOS = Object.keys(ETIQUETA_SEXO) as SexoMascota[];

export const ETIQUETA_TAMANO_MASCOTA: Record<TamanoMascota, string> = {
  pequeño: 'Pequeña',
  mediano: 'Mediana',
  grande: 'Grande',
};

export const TAMANOS_MASCOTA = Object.keys(ETIQUETA_TAMANO_MASCOTA) as TamanoMascota[];

export const ETIQUETA_ENERGIA: Record<EnergiaMascota, string> = {
  baja: 'Energía baja',
  media: 'Energía media',
  alta: 'Energía alta',
};

export const ENERGIAS = Object.keys(ETIQUETA_ENERGIA) as EnergiaMascota[];

export const ETIQUETA_CATEGORIA_EDAD: Record<CategoriaEdad, string> = {
  cachorro: 'Cachorra',
  joven: 'Joven',
  adulto: 'Adulta',
  senior: 'Senior',
};

export const CATEGORIAS_EDAD = Object.keys(ETIQUETA_CATEGORIA_EDAD) as CategoriaEdad[];

// Badge de estado. `danger` está reservado en toda la app a "perdido" (dominio
// de emergencia): aquí no aparece ni para la mascota que ya no está disponible.
// Adoptada se celebra en `forest`, igual que un reencuentro; "en proceso" es un
// aviso en `ochre`, no una mala noticia.
export const ETIQUETA_ESTADO_MASCOTA: Record<EstadoMascota, { texto: string; color: string }> = {
  disponible: { texto: 'En adopción', color: 'bg-forest' },
  en_proceso: { texto: 'En proceso', color: 'bg-ochre' },
  adoptado: { texto: 'Adoptada 💚', color: 'bg-forest' },
};

/** Filtros vacíos del catálogo: todo el mundo entra. `zona: ''` = todas las
 * zonas (no hay default Armenia — se quitó a propósito del resto de la app). */
export const FILTROS_ADOPCION_DEFAULT: FiltrosMascotas = {
  especie: [],
  tamano: [],
  energia: [],
  edad: [],
  zona: '',
};

// Cortes de los tramos de edad, en meses. Son los mismos de
// `EDAD_CATEGORIA_RANGOS` en el backend (cachorro 0-11, joven 12-35, adulto
// 36-83, senior 84+): si cambian allá, cambian aquí.
const MESES_JOVEN = 12;
const MESES_ADULTO = 36;
const MESES_SENIOR = 84;

/** Edad en texto para una tarjeta o una ficha: "5 meses", "1 año", "3 años".
 *
 * ⚠️ Corrige un bug real de la era Adopta, que renderizaba
 * `Math.round(edad_meses / 12)` + " años": un cachorro de 5 meses aparecía como
 * **"0 años"** y uno de 18 como "2 años" (envejecido medio año de gratis).
 *
 * Bajo el año se habla en meses, que es como se habla de un cachorro. Desde el
 * año, los meses sueltos **se truncan**: 18 meses dice "1 año", no "1 año y 6
 * meses". Dos razones: (1) es como habla la gente de la edad —nadie dice que su
 * perro tiene "1 año y 6 meses" salvo que se lo pregunten—, y (2) la tarjeta
 * pone la edad en una línea junto a la raza y la zona, y a 360px una edad de dos
 * unidades empuja el resto fuera. La precisión que importa para adoptar
 * (cachorra / joven / adulta / senior) la lleva `categoriaEdad`, que la tarjeta
 * muestra como chip. Truncar además nunca exagera: "1 año" para 18 meses es
 * cierto; "2 años" no lo era.
 */
export function edadLegible(edadMeses: number): string {
  const meses = Math.max(0, Math.floor(edadMeses));
  if (meses === 0) return 'Menos de 1 mes';
  if (meses < MESES_JOVEN) return meses === 1 ? '1 mes' : `${meses} meses`;
  const anos = Math.floor(meses / 12);
  return anos === 1 ? '1 año' : `${anos} años`;
}

/** Tramo de edad para filtrar y para el chip de la tarjeta. */
export function categoriaEdad(edadMeses: number): CategoriaEdad {
  if (edadMeses < MESES_JOVEN) return 'cachorro';
  if (edadMeses < MESES_ADULTO) return 'joven';
  if (edadMeses < MESES_SENIOR) return 'adulto';
  return 'senior';
}

type AtributosTituloMascota = Pick<Mascota, 'nombre' | 'especie' | 'tamano' | 'raza'>;

/** Título reconocible de una mascota en adopción, mismo espíritu que
 * `tituloReporte`: el nombre manda. La columna `nombre` es obligatoria, pero un
 * formulario puede mandar espacios, y una mascota sin nombre en la tarjeta se
 * ve rota — de ahí la composición de respaldo ("Perro mediano labrador"), que
 * dice más que un hueco. La raza "Otra" no aporta señas y no entra. */
export function tituloMascota(mascota: AtributosTituloMascota): string {
  const nombre = mascota.nombre.trim();
  if (nombre) return nombre;

  const partes = [
    ETIQUETA_ESPECIE_ADOPCION[mascota.especie],
    mascota.tamano,
    mascota.raza && mascota.raza !== 'Otra' ? mascota.raza.toLowerCase() : null,
  ];
  return partes.filter(Boolean).join(' ');
}
