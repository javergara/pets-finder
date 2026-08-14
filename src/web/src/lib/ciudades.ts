// Zonas cubiertas: bounding box + centro de cada una, más el lienzo nacional.
// Duplicado consciente de src/api/reencuentro_api/services/ciudades.py (el
// frontend no consulta estos valores por HTTP) — si cambian allá, cambiar aquí.

export type BoundingBox = {
  latMin: number;
  latMax: number;
  lngMin: number;
  lngMax: number;
  centroLat: number;
  centroLng: number;
};

export const ZONAS: Record<string, BoundingBox> = {
  Armenia: {
    latMin: 4.49,
    latMax: 4.58,
    lngMin: -75.75,
    lngMax: -75.63,
    centroLat: 4.534,
    centroLng: -75.681,
  },
  Pereira: {
    latMin: 4.77,
    latMax: 4.85,
    lngMin: -75.76,
    lngMax: -75.65,
    centroLat: 4.813,
    centroLng: -75.696,
  },
  Manizales: {
    latMin: 5.02,
    latMax: 5.12,
    lngMin: -75.55,
    lngMax: -75.44,
    centroLat: 5.07,
    centroLng: -75.514,
  },
  Cali: {
    latMin: 3.33,
    latMax: 3.5,
    lngMin: -76.6,
    lngMax: -76.44,
    centroLat: 3.452,
    centroLng: -76.532,
  },
  Quibdó: {
    latMin: 5.65,
    latMax: 5.72,
    lngMin: -76.68,
    lngMax: -76.62,
    centroLat: 5.695,
    centroLng: -76.661,
  },
  Bogotá: {
    latMin: 4.55,
    latMax: 4.8,
    lngMin: -74.2,
    lngMax: -74.0,
    centroLat: 4.65,
    centroLng: -74.08,
  },
  // Valle de Aburrá completo: Medellín + Bello (norte) e Itagüí/Envigado (sur).
  Medellín: {
    latMin: 6.13,
    latMax: 6.36,
    lngMin: -75.66,
    lngMax: -75.5,
    centroLat: 6.244,
    centroLng: -75.581,
  },
};

// Lienzo nacional (continental, sin San Andrés): vista agregada del mapa y
// fallback para reportar desde cualquier lugar del país (zona "Otro").
export const COLOMBIA: BoundingBox = {
  latMin: -4.3,
  latMax: 12.6,
  lngMin: -79.1,
  lngMax: -66.9,
  centroLat: 4.6,
  centroLng: -74.1,
};

export const ZONA_OTRO = 'Otro';
export const NOMBRES_ZONAS = Object.keys(ZONAS);

// Landings por zona (feature 46): slug de URL → nombre de zona. Espejo del
// SLUG_ZONAS del backend (routers/paginas.py).
export const SLUGS_ZONA: Record<string, string> = {
  cali: 'Cali',
  armenia: 'Armenia',
  pereira: 'Pereira',
  manizales: 'Manizales',
  quibdo: 'Quibdó',
  bogota: 'Bogotá',
  medellin: 'Medellín',
};

// Ciudades de Colombia para el registro (feature 17): las zonas con mapa propio
// van primero en el select; este resto cubre todas las capitales departamentales
// más las ciudades grandes que no son capital, en orden alfabético.
export const OTRAS_CIUDADES_COLOMBIA = [
  'Arauca',
  'Barrancabermeja',
  'Barranquilla',
  'Bello',
  'Bucaramanga',
  'Buenaventura',
  'Cartagena',
  'Cúcuta',
  'Dosquebradas',
  'Florencia',
  'Ibagué',
  'Inírida',
  'Leticia',
  'Mitú',
  'Mocoa',
  'Montería',
  'Neiva',
  'Palmira',
  'Pasto',
  'Popayán',
  'Puerto Carreño',
  'Riohacha',
  'San Andrés',
  'San José del Guaviare',
  'Santa Marta',
  'Sincelejo',
  'Soacha',
  'Soledad',
  'Tuluá',
  'Tunja',
  'Valledupar',
  'Villavicencio',
  'Yopal',
];

// El lienzo a usar para una zona dada: las 6 conocidas usan su propio bounding
// box; "Otro" (y la vista "Colombia" del mapa) usan el nacional.
export function cajaDeZona(zona: string): BoundingBox {
  return ZONAS[zona] ?? COLOMBIA;
}

// Geolocalización (feature 31): ¿dónde caen unas coords reales?
function dentroDeCaja(caja: BoundingBox, lat: number, lng: number): boolean {
  return lat >= caja.latMin && lat <= caja.latMax && lng >= caja.lngMin && lng <= caja.lngMax;
}

export function coordsEnZona(zona: string, lat: number, lng: number): boolean {
  return dentroDeCaja(cajaDeZona(zona), lat, lng);
}

export function zonaQueContiene(lat: number, lng: number): string | null {
  for (const [nombre, caja] of Object.entries(ZONAS)) {
    if (dentroDeCaja(caja, lat, lng)) return nombre;
  }
  return null;
}
