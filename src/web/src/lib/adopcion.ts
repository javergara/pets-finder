import type { FiltrosMascotas } from '../api/client';
import type {
  AccionSolicitud,
  CategoriaEdad,
  EnergiaMascota,
  EspecieAdopcion,
  EstadoMascota,
  EstadoSolicitud,
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

// ── Copy de las solicitudes de adopción (AD-05) ──────────────────────────────
// La tabla se llama `matches`, pero de cara al usuario esto es siempre una
// **solicitud**. Los dos `Record` van tipados contra su `Literal` de
// `api/types.ts`: si el backend suma un estado o una acción, esto deja de
// compilar hasta que alguien decida su copy — en vez de que un badge muestre
// `undefined` en producción.

/** Badge del estado de una solicitud.
 *
 * `ochre` es "todavía no pasa nada" (esperar no es una mala noticia), `forest`
 * es avanzar, y `cerrado` va en neutro: es el final más frecuente y honesto de
 * una adopción con varias familias interesadas, no un error.
 *
 * ⚠️ **`danger` no aparece y no puede aparecer**: el rojo está reservado en toda
 * la app al dominio de emergencia ("perdido"), y es la misma regla que ya
 * respeta `ETIQUETA_ESTADO_MASCOTA`. Hay un test que lo comprueba estado por
 * estado.
 *
 * El texto es un respaldo estable para listas y chips: el backend manda además
 * una `etiqueta` propia por solicitud ("Sin responder · 5 días"), que depende de
 * los días transcurridos y por eso no se puede calcular aquí.
 *
 * (La forma del badge va en un alias en vez de escrita en línea como en
 * `ETIQUETA_ESTADO_MASCOTA` por una razón mecánica: con el nombre más largo, la
 * anotación completa pasa de 100 columnas y las dos versiones de prettier que
 * conviven en el repo —la del hook y la local— la parten distinto, así que ese
 * bloque cambiaría de forma según quién guarde el archivo.) */
type BadgeSolicitud = { texto: string; color: string };

export const ETIQUETA_ESTADO_SOLICITUD: Record<EstadoSolicitud, BadgeSolicitud> = {
  solicitado: { texto: 'Esperando respuesta', color: 'bg-ochre' },
  en_revision: { texto: 'En revisión', color: 'bg-ochre' },
  visita_agendada: { texto: 'Visita agendada', color: 'bg-forest' },
  adoptado: { texto: 'Adopción cerrada', color: 'bg-forest' },
  cerrado: { texto: 'Solicitud cerrada', color: 'bg-muted' },
};

/** El copy de los cuatro botones de quien publicó la mascota.
 *
 * ⚠️ Este mapeo es **todo** lo que el frontend sabe de la máquina de estados.
 * Qué acciones se pueden ejecutar sobre una solicitud lo decide el backend y
 * llega en `acciones_disponibles`: aquí solo se traduce cada una a su etiqueta.
 * En la era Adopta la pantalla reimplementaba la matriz de transiciones con
 * arrays de estados (`['solicitado','en_revision'].includes(...)`), y las dos
 * fuentes de verdad se separaron en la primera corrección del backend.
 *
 * "Confirmar adopción" en vez de "Aprobar": es irreversible —cierra la mascota y
 * descarta a las demás familias—, así que el botón nombra la consecuencia y no
 * el trámite. */
export const ETIQUETA_ACCION_SOLICITUD: Record<AccionSolicitud, string> = {
  'agendar-visita': 'Agendar visita',
  'pedir-informacion': 'Pedir más información',
  aprobar: 'Confirmar adopción',
  descartar: 'Descartar solicitud',
};

/** Los siete sí/no de una mascota (salud + convivencia) con los mismos valores
 * iniciales de `PetIn`: salud conservadora (no) y convivencia optimista (sí),
 * para no prometer lo que nadie verificó.
 *
 * Viven aquí y no junto a `SeccionesSiNo`, que es quien los pinta, porque son
 * datos del dominio y un módulo que exporta componentes **y** constantes rompe
 * el fast refresh de Vite (lo avisa oxlint). */
export const FLAGS_MASCOTA_INICIALES = {
  esterilizado: false,
  vacunas_al_dia: false,
  microchip: false,
  desparasitado: false,
  apto_ninos: true,
  apto_perros: true,
  apto_gatos: true,
};

export type FlagsMascota = typeof FLAGS_MASCOTA_INICIALES;

/** Filtros vacíos del catálogo: todo el mundo entra. `zona: ''` = todas las
 * zonas (no hay default Armenia — se quitó a propósito del resto de la app). */
export const FILTROS_ADOPCION_DEFAULT: FiltrosMascotas = {
  especie: [],
  tamano: [],
  energia: [],
  edad: [],
  zona: '',
};

/** Cuántas cosas eligió la persona en los filtros del módulo de adopción.
 *
 * Cuenta **valores**, no grupos: elegir perro y gato son dos, y la zona suma uno
 * (`''` = todas las zonas, no cuenta). Es lo que la persona recuerda haber
 * tocado, y es el número que va en el botón plegable ("Filtros · 2").
 *
 * ⚠️ **Fuente de verdad única**, y esa es su razón de existir. Antes de AD-08
 * había dos cuentas paralelas —una en `FiltrosAdopcion` para decidir si mostrar
 * "Limpiar filtros" y otra en `CatalogoAdopcion` para el texto del estado
 * vacío— y **la del catálogo se saltaba `edad`**: con un tramo de edad como
 * único filtro y cero resultados, la pantalla decía "Todavía no hay mascotas
 * publicadas en adopción" en vez de "Ninguna coincide con estos filtros". Le
 * contaba a la persona que el catálogo estaba vacío cuando lo que pasaba es que
 * su filtro no casaba, y le ofrecía publicar una mascota en vez de la salida
 * que necesitaba.
 *
 * Desde el plegado móvil el número importa además por otra razón: con el panel
 * cerrado, es la única señal de que el catálogo está recortado. Si un grupo
 * nuevo de `FiltrosMascotas` no se suma aquí, plegar escondería un filtro
 * activo en silencio. */
export function contarFiltrosActivos(filtros: FiltrosMascotas): number {
  return (
    filtros.especie.length +
    filtros.tamano.length +
    filtros.energia.length +
    filtros.edad.length +
    (filtros.zona === '' ? 0 : 1)
  );
}

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
 * dice más que un hueco. La raza "Otra" no aporta señas y no entra.
 *
 * ⚠️ Espejo de `titulo_pet` (src/api/reencuentro_api/services/titulos.py), que
 * compone el og:title que ven los rastreadores al compartir la ficha. Son la
 * misma regla en dos lenguajes y nada las ata: si cambias esta, cambia la otra
 * (y sus casos, que están escritos iguales a propósito en los dos tests). */
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
