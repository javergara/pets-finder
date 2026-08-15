import { useState } from 'react';
import { mediaUrl } from '../api/client';

/**
 * Galería de fotos con miniaturas (nacida inline en ReporteDetalle, feature 41).
 *
 * La foto grande va sin recorte (`object-contain` con tope de alto): las señas
 * de la mascota pueden estar justo en lo que un crop 4:3 cortaría — decisión de
 * producto de la feature 35, no cosmética.
 *
 * Con una sola foto no se renderizan miniaturas, y con ninguna no renderiza nada.
 */
export function GaleriaFotos({ fotos, alt }: { fotos: string[]; alt: string }) {
  const [fotoActiva, setFotoActiva] = useState(0);

  if (fotos.length === 0) return null;

  // Clamp: la lista de fotos puede encoger entre renders (otro reporte, borrado)
  // y el índice guardado quedaría fuera del array. La miniatura resaltada usa el
  // índice ya clampado para no quedar desincronizada de la foto grande.
  const activa = Math.min(fotoActiva, fotos.length - 1);

  return (
    <div className="flex flex-col gap-2">
      <img
        src={mediaUrl(fotos[activa])}
        alt={alt}
        className="max-h-[75vh] w-full rounded-[22px] border border-line bg-surface-alt object-contain"
      />
      {fotos.length > 1 && (
        <div className="flex gap-2">
          {fotos.map((f, n) => (
            <button
              key={f}
              type="button"
              aria-label={`Ver foto ${n + 1}`}
              onClick={() => setFotoActiva(n)}
              className={`h-16 w-16 overflow-hidden rounded-lg border-2 ${
                n === activa ? 'border-forest' : 'border-line'
              }`}
            >
              <img src={mediaUrl(f)} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
