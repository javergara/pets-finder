// Catálogo de características predefinidas (feature 15): la fuente de verdad de
// las opciones que se ofrecen al reportar y al filtrar. El backend las guarda
// como texto tal cual (columnas nullable), así que reportar y filtrar usan
// exactamente los mismos valores y el match exacto funciona.

export const RAZAS_PERRO = [
  'Criollo / mestizo',
  'Labrador',
  'Golden Retriever',
  'Pastor Alemán',
  'Bulldog',
  'Beagle',
  'Poodle',
  'Pincher',
  'Schnauzer',
  'Husky Siberiano',
  'Chihuahua',
  'Shih Tzu',
  'Pitbull',
  'Rottweiler',
  'Boxer',
  'Otra',
] as const;

export const RAZAS_GATO = [
  'Criollo / mestizo',
  'Siamés',
  'Persa',
  'Angora',
  'Bengalí',
  'Maine Coon',
  'Otra',
] as const;

export const COLORES = [
  'Negro',
  'Blanco',
  'Café',
  'Miel / dorado',
  'Gris',
  'Naranja',
  'Atigrado',
  'Bicolor (manchas)',
  'Tricolor',
  'Otro',
] as const;

export const TAMANOS = ['pequeño', 'mediano', 'grande'] as const;

// La raza solo aplica a perros y gatos; para "otro" (aves, conejos…) no se ofrece.
export function razasPorEspecie(especie: string): readonly string[] {
  if (especie === 'perro') return RAZAS_PERRO;
  if (especie === 'gato') return RAZAS_GATO;
  return [];
}
