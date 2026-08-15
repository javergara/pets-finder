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

// Las fotos que ya están en Storage son las del reporte al publicar (paso 8) y
// las de la propia mascota al editarla (paso 9): el mecanismo es idéntico —no se
// vuelven a subir— pero llamarle "del reporte" a una foto que la persona subió
// aquí sería mentirle. Solo cambia el copy.
const TEXTOS = {
  reporte: {
    titulo: 'Fotos del reporte',
    alt: (n: number) => `Foto ${n} del reporte`,
    quitar: (n: number) => `Quitar la foto ${n} del reporte`,
    ayuda:
      'Se reusan tal cual, sin volver a subirlas. Quita las que no quieras en la ficha de adopción: el reporte las conserva.',
  },
  mascota: {
    titulo: 'Fotos publicadas',
    alt: (n: number) => `Foto ${n} de la mascota`,
    quitar: (n: number) => `Quitar la foto ${n}`,
    ayuda: 'Quita las que ya no la representen y sube otras: en total pueden ser hasta tres.',
  },
} as const;

type Props = {
  // Ya en Storage (del reporte o de la propia ficha): viajan al backend tal cual.
  heredadas: string[];
  onQuitarHeredada: (url: string) => void;
  // Las que se suben aquí, en orden y como lista completa.
  onSubidas: (urls: string[]) => void;
  // De dónde vienen las de arriba. Solo cambia el copy, no el comportamiento.
  origen?: keyof typeof TEXTOS;
};

export function FotosMascota({
  heredadas,
  onQuitarHeredada,
  onSubidas,
  origen = 'reporte',
}: Props) {
  const cupo = MAX_FOTOS - heredadas.length;
  const textos = TEXTOS[origen];

  return (
    <div className="flex flex-col gap-2">
      {heredadas.length > 0 && (
        <>
          <p className="text-sm font-medium text-ink-soft">{textos.titulo}</p>
          <div className="flex flex-wrap gap-2">
            {heredadas.map((url, n) => (
              <div key={url} className="relative">
                <img
                  src={mediaUrl(url)}
                  alt={textos.alt(n + 1)}
                  className="h-20 w-20 rounded-lg border border-line object-cover"
                />
                <button
                  type="button"
                  aria-label={textos.quitar(n + 1)}
                  onClick={() => onQuitarHeredada(url)}
                  className="absolute -right-2 -top-2 h-6 w-6 rounded-full border border-line bg-surface text-xs text-ink-soft"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          <p className="text-xs text-muted">{textos.ayuda}</p>
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
