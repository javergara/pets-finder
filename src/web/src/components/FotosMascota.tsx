import { mediaUrl } from '../api/client';
import { FotoUpload } from './FotoUpload';

// Las fotos de una mascota en adopción (AD-02): hasta tres, y algunas pueden
// venir heredadas de un reporte encontrado.
//
// Heredar significa **no volver a subirlas**: son URLs que ya están en Storage,
// del reporte que sigue vivo. Re-subirlas duplicaría archivos en un bucket
// gratuito y, peor, el borrado de la mascota (paso 2) da por hecho que las fotos
// con `report_id` no son suyas. Aquí se pintan como miniaturas propias del
// formulario, con su botón de quitar, y `FotoUpload` solo cubre el cupo que
// sobra.
//
// ⚠️ `FotoUpload` cambia de contrato según `maxFotos`: con 2 o 3 avisa por
// `onFotosSubidas` con la lista completa (y después por `onFotoSubida` con la
// principal, que aquí sería un retroceso), pero con **1** entra en modo de foto
// única y solo llama a `onFotoSubida`. Escuchar un solo callback pierde fotos en
// silencio, según cuántas se hayan heredado.

const MAX_FOTOS = 3;

type Props = {
  // Ya en Storage (del reporte): viajan al backend tal cual.
  heredadas: string[];
  onQuitarHeredada: (url: string) => void;
  // Las que se suben aquí, en orden y como lista completa.
  onSubidas: (urls: string[]) => void;
};

export function FotosMascota({ heredadas, onQuitarHeredada, onSubidas }: Props) {
  const cupo = MAX_FOTOS - heredadas.length;

  return (
    <div className="flex flex-col gap-2">
      {heredadas.length > 0 && (
        <>
          <p className="text-sm font-medium text-ink-soft">Fotos del reporte</p>
          <div className="flex flex-wrap gap-2">
            {heredadas.map((url, n) => (
              <div key={url} className="relative">
                <img
                  src={mediaUrl(url)}
                  alt={`Foto ${n + 1} del reporte`}
                  className="h-20 w-20 rounded-lg border border-line object-cover"
                />
                <button
                  type="button"
                  aria-label={`Quitar la foto ${n + 1} del reporte`}
                  onClick={() => onQuitarHeredada(url)}
                  className="absolute -right-2 -top-2 h-6 w-6 rounded-full border border-line bg-surface text-xs text-ink-soft"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          <p className="text-xs text-muted">
            Se reusan tal cual, sin volver a subirlas. Quita las que no quieras en la ficha de
            adopción: el reporte las conserva.
          </p>
        </>
      )}

      {cupo > 0 && (
        <FotoUpload
          maxFotos={cupo}
          onFotoSubida={(url) => {
            if (cupo === 1) onSubidas([url]);
          }}
          onFotosSubidas={onSubidas}
        />
      )}
    </div>
  );
}
