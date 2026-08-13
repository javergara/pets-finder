import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { type ReactNode, useEffect, useRef } from 'react';
import { cajaDeZona } from '../lib/ciudades';

export type PinMapa = {
  id: number | string;
  lat: number;
  lng: number;
  // Token de color del design-system (perdido=bg-danger, encontrado=bg-forest).
  colorClass: string;
  etiqueta: string;
  onClick?: () => void;
};

// Hex reales de los tokens (src/web/src/index.css) — Leaflet pinta SVG, no clases.
const COLOR_POR_CLASE: Record<string, string> = {
  'bg-danger': '#9b3b2e',
  'bg-forest': '#1f4d3a',
  // Red de apoyo (feature 32): acopio=ochre, tienda=ink; el fallback sigue ochre.
  'bg-ochre': '#b57c2e',
  'bg-ink': '#1b1a17',
};

type Props = {
  zona: string;
  pines: PinMapa[];
  // Si se pasa, un click en el mapa devuelve las coords reales del punto —
  // así se ubica el pin de un reporte nuevo.
  onClickCoords?: (coords: { lat: number; lng: number }) => void;
  // Al cambiar, el mapa se centra ahí (feature 31: "mi ubicación").
  centro?: { lat: number; lng: number } | null;
  children?: ReactNode;
};

function redondear(valor: number): number {
  return Math.round(valor * 10000) / 10000;
}

// Mapa real con Leaflet + tiles de OpenStreetMap (ADR 0008): gratis, sin API key.
// Además del mapa, cada pin se renderiza como botón accesible (sr-only) — es la
// ruta para lectores de pantalla y lo que ejercitan los tests (Leaflet no se
// inicializa en Vitest/jsdom, ver el guard de MODE==='test').
export function MapaLienzo({ zona, pines, onClickCoords, centro, children }: Props) {
  const contenedorRef = useRef<HTMLDivElement>(null);
  const mapaRef = useRef<L.Map | null>(null);
  const capaPinesRef = useRef<L.LayerGroup | null>(null);
  const onClickCoordsRef = useRef(onClickCoords);
  onClickCoordsRef.current = onClickCoords;

  useEffect(() => {
    // jsdom no puede medir el contenedor ni cargar tiles: en tests el mapa real
    // no se monta y el contrato del componente se verifica por la lista sr-only.
    if (import.meta.env.MODE === 'test') return;
    if (!contenedorRef.current || mapaRef.current) return;

    const mapa = L.map(contenedorRef.current);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(mapa);
    mapa.on('click', (e: L.LeafletMouseEvent) => {
      onClickCoordsRef.current?.({
        lat: redondear(e.latlng.lat),
        lng: redondear(e.latlng.lng),
      });
    });
    capaPinesRef.current = L.layerGroup().addTo(mapa);
    mapaRef.current = mapa;

    return () => {
      mapa.remove();
      mapaRef.current = null;
      capaPinesRef.current = null;
    };
  }, []);

  useEffect(() => {
    const caja = cajaDeZona(zona);
    mapaRef.current?.fitBounds([
      [caja.latMin, caja.lngMin],
      [caja.latMax, caja.lngMax],
    ]);
  }, [zona]);

  // "Mi ubicación" (feature 31): centrar sin cambiar el encuadre de zona.
  useEffect(() => {
    if (!centro) return;
    mapaRef.current?.setView([centro.lat, centro.lng], 15);
  }, [centro]);

  useEffect(() => {
    const capa = capaPinesRef.current;
    if (!capa) return;
    capa.clearLayers();
    for (const pin of pines) {
      const marcador = L.circleMarker([pin.lat, pin.lng], {
        radius: 9,
        color: '#fffdf8',
        weight: 2,
        fillColor: COLOR_POR_CLASE[pin.colorClass] ?? '#b57c2e',
        fillOpacity: 1,
      });
      marcador.bindTooltip(pin.etiqueta);
      if (pin.onClick) {
        marcador.on('click', pin.onClick);
      }
      marcador.addTo(capa);
    }
  }, [pines]);

  return (
    <div className="relative">
      <div
        ref={contenedorRef}
        data-testid="mapa-lienzo"
        className={`aspect-4/3 w-full overflow-hidden rounded-2xl border border-line bg-surface-alt ${
          onClickCoords ? 'cursor-crosshair' : ''
        }`}
      />
      {/* Equivalente accesible del mapa: un botón real por pin. */}
      <ul className="sr-only">
        {pines.map((pin) => (
          <li key={pin.id}>
            <button
              type="button"
              className={pin.colorClass}
              aria-label={pin.etiqueta}
              onClick={pin.onClick}
            >
              {pin.etiqueta}
            </button>
          </li>
        ))}
      </ul>
      {children}
    </div>
  );
}
