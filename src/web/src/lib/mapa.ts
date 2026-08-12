// Mapa propio en CSS/SVG puro: sin dependencia externa (Leaflet/Google Maps/OSM)
// ni conexión a internet en runtime (ADR 0005 §5). Los pines se posicionan
// interpolando linealmente lat/lng dentro del bounding box de la zona activa
// (lib/ciudades.ts), y la interpolación es invertible: un click en el lienzo
// (fracciones 0-1 de ancho/alto) se convierte de vuelta en lat/lng para poner
// el pin de un reporte.
import { cajaDeZona } from './ciudades';

// Redondeado a 4 decimales: suficiente precisión para posicionar un pin y evita que
// errores de punto flotante de JS (p. ej. 0.19999999999999432 en vez de 0.2) se filtren
// como porcentajes CSS con ruido (`50.00000000000355%` en vez de `50%`).
function redondear(valor: number): number {
  return Math.round(valor * 10000) / 10000;
}

export function posicionEnMapa(
  lat: number,
  lng: number,
  zona: string,
): { left: string; top: string } {
  const caja = cajaDeZona(zona);
  const left = ((lng - caja.lngMin) / (caja.lngMax - caja.lngMin)) * 100;
  // Eje lat invertido: mayor lat = más al norte = arriba (top más pequeño).
  const top = ((caja.latMax - lat) / (caja.latMax - caja.latMin)) * 100;
  return { left: `${redondear(left)}%`, top: `${redondear(top)}%` };
}

// Inversa de posicionEnMapa: fracciones 0-1 medidas sobre el lienzo (x desde la
// izquierda, y desde arriba, vía getBoundingClientRect) → lat/lng.
export function coordsDesdeFraccion(
  fx: number,
  fy: number,
  zona: string,
): { lat: number; lng: number } {
  const caja = cajaDeZona(zona);
  const lng = caja.lngMin + fx * (caja.lngMax - caja.lngMin);
  const lat = caja.latMax - fy * (caja.latMax - caja.latMin);
  return { lat: redondear(lat), lng: redondear(lng) };
}
