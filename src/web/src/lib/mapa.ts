// Mapa propio en CSS/SVG puro: sin dependencia externa (Leaflet/Google Maps/OSM)
// ni conexión a internet en runtime (ADR 0005 §5). Los pines se posicionan
// interpolando linealmente lat/lng dentro de un bounding box.
//
// Versión provisional de la feature 01 fijada al bounding box de Bogotá; la
// feature 04-reportar-ui la parametriza por zona (lib/ciudades.ts, en sync con
// services/ciudades.py del backend) y añade la inversa coordsDesdeFraccion
// para poner un pin con click.
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
