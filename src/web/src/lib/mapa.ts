// Mapa propio en CSS/SVG puro (feature 14-shelter-map): sin dependencia externa
// (Leaflet/Google Maps/OSM) ni conexión a internet en runtime. Los pines se
// posicionan interpolando linealmente lat/lng dentro del bounding box de Bogotá.
//
// Estas constantes duplican intencionalmente BOGOTA_LAT_RANGE/BOGOTA_LNG_RANGE de
// scripts/seed.py -- deben mantenerse en sync si ese bounding box cambia.
const LAT_MIN = 4.55;
const LAT_MAX = 4.8;
const LNG_MIN = -74.2;
const LNG_MAX = -74.0;

// Redondeado a 4 decimales: suficiente precisión para posicionar un pin y evita que
// errores de punto flotante de JS (p. ej. 0.19999999999999432 en vez de 0.2) se filtren
// como porcentajes CSS con ruido (`50.00000000000355%` en vez de `50%`).
function redondear(valor: number): number {
  return Math.round(valor * 10000) / 10000;
}

export function posicionEnMapa(lat: number, lng: number): { left: string; top: string } {
  const left = ((lng - LNG_MIN) / (LNG_MAX - LNG_MIN)) * 100;
  // Eje lat invertido: mayor lat = más al norte = arriba (top más pequeño).
  const top = ((LAT_MAX - lat) / (LAT_MAX - LAT_MIN)) * 100;
  return { left: `${redondear(left)}%`, top: `${redondear(top)}%` };
}
