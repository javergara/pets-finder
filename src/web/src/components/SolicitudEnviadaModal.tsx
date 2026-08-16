import { Link } from 'react-router-dom';
import { mediaUrl } from '../api/client';
import type { SolicitudResumen } from '../api/types';

// Acuse de recibo del swipe-derecha (AD-05): el backend crea la solicitud en el
// mismo commit que el swipe y la devuelve en `SwipeOut.solicitud`. Sin este
// aviso, "Me interesa" se siente exactamente igual que "Ahora no" y nadie sabe
// que acaba de pedir una mascota ni dónde seguirla.
//
// Port de `MatchModal` de la era Adopta (`adopta-v1`), con tres cambios:
//
// 1. **Se le quitó la clase `[animation:popIn_.24s_cubic-bezier(...)]`**, y no
//    por gusto: `@keyframes popIn` no está definido ni en el `index.css` de
//    adopta-v1 ni en el de este repo, así que era una animación muerta que
//    nadie notó nunca. Dejarla al portar habría arrastrado una promesa falsa —
//    y quien la viera en el diff asumiría que el modal ya tiene entrada
//    animada. Si algún día se quiere, se define el keyframe primero.
// 2. El copy no menciona "match" ni "refugio": esto es una **solicitud** y
//    quien publica puede ser una organización o un rescatista. Tampoco promete
//    un tiempo de respuesta ("suelen responder en 24 horas"): ese dato no
//    existe en este producto y prometerlo sería inventarlo.
// 3. La acción principal es un `Link` de verdad, no un `onClick` que navega:
//    así se puede abrir en otra pestaña y el teclado la alcanza como enlace.
//
// El resumen que llega (`SolicitudResumen`) no trae publicador ni afinidad a
// propósito: para eso está el detalle. Aquí solo hace falta la mascota.

type Props = {
  solicitud: SolicitudResumen;
  /** Cerrar y volver al deck, que sigue vivo debajo con la carta siguiente. */
  onSeguirViendo: () => void;
};

export function SolicitudEnviadaModal({ solicitud, onSeguirViendo }: Props) {
  const nombre = solicitud.pet.nombre;
  const foto = solicitud.pet.fotos[0];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Solicitud enviada para ${nombre}`}
      className="fixed inset-0 z-20 flex items-center justify-center bg-[rgba(27,26,23,.42)] p-6"
    >
      <div className="w-full max-w-105 rounded-2xl border border-line bg-surface p-8 text-center">
        <p className="font-mono text-xs tracking-wide text-muted uppercase">Solicitud enviada</p>
        {foto && (
          <img
            src={mediaUrl(foto)}
            alt={`Foto de ${nombre}`}
            className="mx-auto mt-4 h-28 w-28 rounded-full object-cover"
          />
        )}
        <h2 className="mt-4 font-display text-2xl text-ink">Ya pediste a {nombre}</h2>
        <p className="mt-2 text-sm text-ink-soft">
          Quien la publicó recibió tu solicitud y podrá ver tu cuestionario de hogar para
          responderte. Mientras tanto puedes seguir mirando otras mascotas.
        </p>
        <div className="mt-6 flex flex-col gap-2">
          <Link
            to="/adoptar/mis-solicitudes"
            className="rounded-full bg-forest px-4 py-3 font-medium text-bg"
          >
            Ver mis solicitudes
          </Link>
          <button
            type="button"
            onClick={onSeguirViendo}
            className="rounded-full px-4 py-3 font-medium text-muted"
          >
            Seguir viendo mascotas
          </button>
        </div>
      </div>
    </div>
  );
}
