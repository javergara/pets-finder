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
  // Puente con adopción (AD-02): la mascota que se publicó desde este reporte.
  // Solo llega con algo en el DETALLE (`GET /api/reports/{id}`); en el listado y
  // el mapa el backend lo deja siempre en `null` a propósito (llenarlo ahí sería
  // una query por reporte). Opcional en el tipo, como `fotos`, para no obligar a
  // cada fixture de test a declararlo.
  adopcion_pet_id?: number | null;
};

/** `parecido_foto` es la banda visual del ADR 0012 — nunca un porcentaje: el
 * modelo no da una probabilidad y un número alto y equivocado llevaría a
 * entregarle una mascota a quien no es. Ausente cuando no hay evidencia visual.
 * Se llama así y no `parecido` porque `ResultadoBusqueda.parecido` ya existe y
 * es un 0-100 de otra cosa (feature 38). */
export type Coincidencia = Reporte & {
  distancia_km: number;
  razones: string[];
  parecido_foto: 'alto' | 'medio' | null;
};

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

export type TipoOrganizacion =
  | 'centro_acopio'
  | 'fundacion'
  | 'tienda'
  | 'veterinaria'
  | 'entrenador';

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

// ─────────────────────────────────────────────────────────────────────────────
// Módulo de adopción (AD-01) — espejo de `src/api/reencuentro_api/schemas/pet.py`
//
// Convención de nombres del módulo, y no es cosmética: `Reporte` es el dominio
// de perdidos/encontrados (tabla `reports`) y **`Mascota` es el dominio de
// adopción** (tabla `pets`, `Pet` en Python). La ambigüedad es real — este repo
// ya tiene pantallas llamadas `BuscarMascota` y `ReportarMascota` que son del
// dominio de emergencia, no de este.
//
// Estos tipos son un espejo puro de los schemas: si un campo no está en
// `PetOut`, no está aquí. Los **valores** (catálogos de copy, etiquetas y
// funciones puras como `edadLegible`) viven en `src/lib/adopcion.ts`, porque
// este archivo no exporta valores.
// ─────────────────────────────────────────────────────────────────────────────

export type EspecieAdopcion = 'perro' | 'gato' | 'otro';
export type SexoMascota = 'macho' | 'hembra';
export type TamanoMascota = 'pequeño' | 'mediano' | 'grande';
export type EnergiaMascota = 'baja' | 'media' | 'alta';
export type EstadoMascota = 'disponible' | 'en_proceso' | 'adoptado';

// Tramo de edad para filtrar el catálogo. No es una columna: se deriva de
// `edad_meses` con `categoriaEdad()` (`lib/adopcion.ts`), que es donde viven los
// cortes. Los valores son los que espera `services/filtros.py` (AD-03).
export type CategoriaEdad = 'cachorro' | 'joven' | 'adulto' | 'senior';

/** Quién publica la mascota, en un solo objeto (espejo de `PublicadorOut`):
 * `id` es el de la organización o el del rescatista, según `tipo`. */
export type Publicador = {
  tipo: 'organizacion' | 'rescatista';
  id: number;
  nombre: string;
  telefono_contacto: string | null;
  zona: string | null;
  ciudad_texto: string | null;
  barrio: string | null;
  foto_url: string | null;
};

/** Qué tan bien encaja la mascota con el hogar de quien mira (`AfinidadOut`).
 * Siempre `null` hasta AD-03. */
export type Afinidad = {
  score: number;
  explicacion: string;
  razones: string[];
  incompatible: boolean;
};

export type Mascota = {
  id: number;
  organizacion_id: number | null;
  // ⚠️ El rescatista que publicó la mascota, NUNCA el adoptante que la mira
  // (en la era Adopta significaba lo contrario). El adoptante viaja aparte,
  // como `adoptante_id`, y nunca se guarda en la mascota.
  user_id: number | null;
  // Puente con el reporte de "encontrada" del que salió (AD-02).
  report_id: number | null;
  nombre: string;
  especie: EspecieAdopcion;
  raza: string | null;
  sexo: SexoMascota;
  edad_meses: number;
  tamano: TamanoMascota;
  energia: EnergiaMascota;
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
  zona: string;
  ciudad_texto: string | null;
  barrio: string | null;
  lat: number | null;
  lng: number | null;
  telefono_contacto: string | null;
  estado: EstadoMascota;
  publicado_en: string;
  adoptado_en: string | null;
  // Calculados por el router, no columnas. En AD-01 solo `publicador` trae algo;
  // el resto llega con AD-03 (afinidad), AD-05 (solicitud) y AD-07 (favoritos).
  publicador: Publicador | null;
  afinidad: Afinidad | null;
  es_favorito: boolean;
  ya_solicitada: boolean;
  distancia_km: number | null;
};

export type MascotaIn = {
  // ⚠️ Quien hace el request (autoría → 403 en el backend). El dueño se declara
  // aparte y es exclusivo: `organizacion_id` **o** `rescatista_id`, nunca ambos
  // ni ninguno (422). `rescatista_id` es el que se persiste en `Mascota.user_id`.
  user_id: number;
  organizacion_id?: number;
  rescatista_id?: number;
  nombre: string;
  especie: EspecieAdopcion;
  sexo: SexoMascota;
  tamano: TamanoMascota;
  energia: EnergiaMascota;
  raza?: string;
  edad_meses: number;
  historia: string;
  tags?: string[];
  fotos?: string[];
  esterilizado?: boolean;
  vacunas_al_dia?: boolean;
  microchip?: boolean;
  desparasitado?: boolean;
  apto_ninos?: boolean;
  apto_perros?: boolean;
  apto_gatos?: boolean;
  zona: string;
  ciudad_texto?: string;
  barrio?: string;
  lat?: number;
  lng?: number;
  // Obligatorio cuando publica un rescatista: el usuario no tiene teléfono y sin
  // esto la mascota es incontactable.
  telefono_contacto?: string;
  report_id?: number;
};

/** Edición parcial de una mascota publicada (espejo de `PetUpdate`, AD-02).
 *
 * ⚠️ **No lleva `zona` ni `ciudad_texto`, y no es un olvido**: `PetUpdate` los
 * omite a propósito, así que el backend los ignoraría. Mudar una mascota de zona
 * cambiaría su encuadre en el mapa; para eso se despublica y se vuelve a
 * publicar. Por la misma razón tampoco se puede cambiar el publicador
 * (`organizacion_id` / `rescatista_id`).
 *
 * `user_id` no es editable: identifica a **quien pide el cambio** para que el
 * router valide autoría (403 si no es quien publicó). Nunca es el adoptante.
 *
 * ⚠️ `fotos` y `tags` se mandan como la lista completa que debe quedar, no como
 * un incremento. Y como el backend aplica `exclude_none=True`, omitir un campo y
 * mandarlo en `null` son lo mismo: no hay forma de vaciar un opcional por aquí.
 */
export type MascotaUpdate = {
  user_id: number;
  nombre?: string;
  especie?: EspecieAdopcion;
  sexo?: SexoMascota;
  tamano?: TamanoMascota;
  energia?: EnergiaMascota;
  raza?: string;
  edad_meses?: number;
  historia?: string;
  tags?: string[];
  fotos?: string[];
  esterilizado?: boolean;
  vacunas_al_dia?: boolean;
  microchip?: boolean;
  desparasitado?: boolean;
  apto_ninos?: boolean;
  apto_perros?: boolean;
  apto_gatos?: boolean;
  barrio?: string;
  lat?: number;
  lng?: number;
  telefono_contacto?: string;
  estado?: EstadoMascota;
};

// ─────────────────────────────────────────────────────────────────────────────
// Deck de descubrimiento (AD-03) — espejo de `schemas/swipe.py`
// ─────────────────────────────────────────────────────────────────────────────

/** Qué decidió quien mira el deck sobre una mascota.
 *
 * Los valores persistidos son `like`/`pass` (columna `swipes.direccion`), pero
 * el copy visible es **"Me interesa" / "Ahora no"** y nunca "rechazar": el match
 * no es mutuo (ADR 0002), así que un `pass` no rechaza a nadie — solo saca esa
 * tarjeta del deck de esa persona. */
export type DireccionSwipe = 'like' | 'pass';

export type Swipe = {
  id: number;
  // ⚠️ El ADOPTANTE que miró el deck, no quien publicó la mascota (eso es
  // `Mascota.user_id`). Las dos son FK a `users.id` y ninguna base avisa si se
  // cruzan: mismo aviso que llevan el modelo, el schema y el router.
  user_id: number;
  pet_id: number;
  direccion: DireccionSwipe;
  creado_en: string;
  // Siempre `null` en AD-03: el swipe no crea nada más. La solicitud (tabla
  // `matches`, "solicitud" en el copy) la crea AD-05, que ampliará este campo a
  // `SolicitudResumen | null` cuando ese schema exista. Se tipa como `null` a
  // propósito: inventarle hoy una forma que nada llena sería declarar un
  // contrato que el backend no cumple.
  solicitud: null;
};

/** Tarjeta mínima de la franja de celebración (espejo de `PetResumenOut`): el
 * resumen de adopciones NO devuelve la mascota completa. */
export type MascotaResumen = {
  id: number;
  nombre: string;
  especie: EspecieAdopcion;
  raza: string | null;
  edad_meses: number;
  fotos: string[];
  estado: EstadoMascota;
};

/** La métrica de esperanza del módulo, espejo de `ReunidosResumen`. */
export type AdopcionesResumen = {
  total: number;
  recientes: MascotaResumen[];
};

/** El cuestionario de hogar de quien adopta (espejo de `HomeProfileOut`, AD-04).
 *
 * Es la entrada del cálculo de afinidad: sin él el deck responde igual, pero
 * con `afinidad: null` en todas las tarjetas.
 *
 * `presupuesto_mensual_cop` es `null` cuando la persona no quiso decirlo —
 * decisión de producto, no un dato faltante: `services/afinidad.py` degrada a
 * solo-experiencia. Nada de rellenarlo con un número por defecto en la UI. */
export type PerfilHogar = {
  user_id: number;
  vivienda: ViviendaHogar;
  espacio_exterior: EspacioExterior;
  personas_en_casa: number;
  tiene_ninos: boolean;
  tiene_otros_perros: boolean;
  tiene_otros_gatos: boolean;
  horas_fuera_dia: number;
  experiencia_previa: ExperienciaPrevia;
  presupuesto_mensual_cop: number | null;
  preferencia_especies: EspecieAdopcion[];
  preferencia_tamanos: TamanoMascota[];
  preferencia_energia: EnergiaMascota;
};

export type ViviendaHogar = 'apartamento' | 'casa';
export type EspacioExterior = 'ninguno' | 'patio' | 'jardin';
export type ExperienciaPrevia = 'ninguna' | 'algo' | 'mucha';

/** Lo que viaja en el `PUT` (espejo de `HomeProfileIn`).
 *
 * ⚠️ `user_id` es redundante con el de la ruta a propósito: el backend compara
 * los dos y responde 403 si no coinciden.
 *
 * El presupuesto es el único campo opcional: omitirlo y mandarlo en `null`
 * significan lo mismo, y el backend acepta las dos formas. */
export type PerfilHogarIn = Omit<PerfilHogar, 'presupuesto_mensual_cop'> & {
  presupuesto_mensual_cop?: number | null;
};
