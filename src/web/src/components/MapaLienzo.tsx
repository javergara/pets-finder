import { type MouseEvent, type ReactNode } from 'react';
import { coordsDesdeFraccion, posicionEnMapa } from '../lib/mapa';

export type PinMapa = {
  id: number | string;
  lat: number;
  lng: number;
  // Token de color de fondo (design-system: perdido=bg-danger, encontrado=bg-forest).
  colorClass: string;
  etiqueta: string;
  onClick?: () => void;
};

type Props = {
  zona: string;
  pines: PinMapa[];
  // Si se pasa, un click en el lienzo (fuera de un pin) devuelve las coords
  // interpoladas — así se pone el pin de un reporte nuevo.
  onClickCoords?: (coords: { lat: number; lng: number }) => void;
  children?: ReactNode;
};

// Lienzo del mapa propio en CSS puro (ADR 0005 §5): sin tiles ni red en runtime.
// El bounding box activo lo decide `zona` (lib/ciudades.ts); "Colombia"/"Otro"
// usan el lienzo nacional.
export function MapaLienzo({ zona, pines, onClickCoords, children }: Props) {
  function handleClick(e: MouseEvent<HTMLDivElement>) {
    if (!onClickCoords) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const fx = (e.clientX - rect.left) / rect.width;
    const fy = (e.clientY - rect.top) / rect.height;
    onClickCoords(coordsDesdeFraccion(fx, fy, zona));
  }

  return (
    // biome/oxlint: el click del lienzo es progresivo — cada acción tiene su
    // alternativa accesible (inputs de zona/coords en el formulario).
    <div
      data-testid="mapa-lienzo"
      onClick={handleClick}
      className={`relative w-full overflow-hidden rounded-2xl border border-line bg-surface-alt ${
        onClickCoords ? 'cursor-crosshair' : ''
      } aspect-4/3`}
    >
      {/* Retícula sutil para dar sensación de mapa sin tiles externos. */}
      <div
        aria-hidden
        className="absolute inset-0"
        style={{
          backgroundImage:
            'linear-gradient(#e4ddce66 1px, transparent 1px), linear-gradient(90deg, #e4ddce66 1px, transparent 1px)',
          backgroundSize: '2rem 2rem',
        }}
      />
      {pines.map((pin) => {
        const { left, top } = posicionEnMapa(pin.lat, pin.lng, zona);
        return (
          <button
            key={pin.id}
            type="button"
            title={pin.etiqueta}
            aria-label={pin.etiqueta}
            onClick={(e) => {
              e.stopPropagation();
              pin.onClick?.();
            }}
            className={`absolute h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-bg shadow ${pin.colorClass}`}
            style={{ left, top }}
          />
        );
      })}
      {children}
    </div>
  );
}
