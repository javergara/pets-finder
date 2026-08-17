import { Link } from 'react-router-dom';
import { mediaUrl } from '../api/client';
import type { Solicitud } from '../api/types';
import { ETIQUETA_ESTADO_SOLICITUD } from '../lib/adopcion';

// Las filas de una lista de solicitudes de adopción (AD-05). Las comparten la
// pantalla `MisSolicitudes` (sus dos secciones) y el panel de una organización
// dentro de su ficha: son la misma fila mirada desde los dos lados, y una
// segunda copia se habría desincronizado en el primer cambio de copy.
//
// Lo único que cambia entre los dos lados es **quién es la otra persona**, y por
// eso viaja como prop en vez de deducirse: una solicitud trae siempre las dos
// partes (`publicador` y `adoptante`), así que el componente no puede adivinar
// desde dónde lo están mirando — y equivocarse sería enseñarle a alguien su
// propio nombre como si fuera el de la contraparte.
//
// ⚠️ El componente **no decide nada**: no filtra por estado ni esconde filas.
// Qué se puede hacer con cada solicitud lo manda el backend en
// `acciones_disponibles`, y los botones viven en el detalle (paso 7).
//
// Paleta `forest`/`ochre`/`muted` vía `ETIQUETA_ESTADO_SOLICITUD`: el rojo está
// reservado en toda la app al dominio de emergencia ("perdido") y no entra aquí,
// tampoco en una solicitud cerrada.

type Props = {
  solicitudes: Solicitud[];
  /** `enviada` = la mandé yo (veo de quién es la mascota); `recibida` = me la
   * mandaron a mí (veo quién la pidió). */
  perspectiva: 'enviada' | 'recibida';
};

/** Quién está al otro lado de esta solicitud, ya en copy.
 *
 * `publicador` puede ser `null` de verdad —la organización que publicó la
 * mascota pudo eliminarse (feature 32)— y en ese caso la fila lo dice en vez de
 * dejar un hueco: quien envió la solicitud merece saber por qué nadie responde.
 */
function contraparte(solicitud: Solicitud, perspectiva: Props['perspectiva']): string {
  if (perspectiva === 'recibida') return `Pedida por ${solicitud.adoptante.nombre}`;
  return solicitud.publicador
    ? `Publicada por ${solicitud.publicador.nombre}`
    : 'Publicada por un lugar que ya no está en la app';
}

export function ListaSolicitudes({ solicitudes, perspectiva }: Props) {
  return (
    <ul className="space-y-3">
      {solicitudes.map((solicitud) => {
        const badge = ETIQUETA_ESTADO_SOLICITUD[solicitud.estado];
        const foto = solicitud.pet.fotos[0];
        return (
          <li
            key={solicitud.id}
            className="flex flex-wrap items-center gap-4 rounded-2xl border border-line bg-surface p-4"
          >
            <span
              className="h-16 w-16 shrink-0 rounded-xl bg-surface-alt bg-cover bg-center"
              style={{ backgroundImage: foto ? `url(${mediaUrl(foto)})` : undefined }}
            />
            <div className="min-w-0 flex-1">
              {/* El enlace envuelve solo el nombre: la fila entera como enlace
                  dejaría el badge y el estado dentro de su nombre accesible. */}
              <Link
                to={`/adoptar/solicitud/${solicitud.id}`}
                className="font-display text-lg text-ink"
              >
                {solicitud.pet.nombre}
              </Link>
              <p className="text-sm text-muted">{contraparte(solicitud, perspectiva)}</p>
              {/* La `etiqueta` la calcula el backend con los días transcurridos
                  ("Sin responder · 5 días") y por eso no se puede reconstruir
                  aquí. Solo se muestra cuando aporta algo sobre el badge: en los
                  estados cerrados las dos dicen lo mismo y repetirlo es ruido. */}
              {solicitud.etiqueta !== badge.texto && (
                <p className="text-sm text-muted">{solicitud.etiqueta}</p>
              )}
            </div>
            <span
              className={`shrink-0 rounded-md px-3 py-1 font-mono text-xs tracking-wide text-bg ${badge.color}`}
            >
              {badge.texto}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
