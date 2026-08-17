import { type ReactNode, useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { ApiError, listarSolicitudes } from '../api/client';
import type { Solicitud } from '../api/types';
import { ListaSolicitudes } from '../components/ListaSolicitudes';
import { getActiveUserId, hasActiveUser } from '../lib/session';

// Las dos mitades de una adopción en una sola pantalla (AD-05): lo que pediste y
// lo que te pidieron. Son la misma entidad vista desde los dos lados, y separar
// la segunda en otra ruta obligaría a quien rescata —que casi siempre también
// busca— a recordar dos direcciones.
//
// ⚠️ **Gate de cuenta antes de leer ningún id**, igual que `MisReportes` y por la
// misma razón, agravada: esta pantalla no compara autoría, *consulta* por el id
// activo, y sin cuenta `getActiveUserId()` cae al `DEMO_USER_ID = 1`, que en
// producción es una persona real. Un visitante anónimo leería las solicitudes de
// esa persona, y una solicitud lleva el nombre de quien la envió (y su mensaje y
// su teléfono en el detalle). No basta con esconder botones: hay que no
// preguntar. Por eso el `if (!conCuenta) return` vive también dentro del efecto —
// el `<Navigate>` se renderiza, pero los efectos corren igual después del commit.
//
// Las dos listas se piden juntas y comparten error: salen del mismo endpoint, y
// si una falla por red o por un 403 la otra iba a fallar igual. Un solo aviso
// dice la verdad sin repetirla dos veces.
//
// Paleta `forest`/`ochre`/`muted` (los badges los pone `ListaSolicitudes`): el
// rojo está reservado en toda la app a "perdido" y no entra en el módulo de
// adopción, tampoco en el bloque de error.

const MENSAJE_ERROR = 'No pudimos cargar tus solicitudes. Revisa tu conexión e intenta de nuevo.';

/** La ruta propia, para el `?volver=` del registro: quien se registra desde aquí
 * vuelve aquí. */
const RUTA = '/adoptar/mis-solicitudes';

export function MisSolicitudes() {
  const conCuenta = hasActiveUser();
  const userId = getActiveUserId();
  const [enviadas, setEnviadas] = useState<Solicitud[] | null>(null);
  const [recibidas, setRecibidas] = useState<Solicitud[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!conCuenta) return;
    setError(null);
    Promise.all([
      listarSolicitudes({ adoptanteId: userId }),
      listarSolicitudes({ publicadorId: userId }),
    ])
      .then(([mias, ajenas]) => {
        setEnviadas(mias);
        setRecibidas(ajenas);
      })
      // El backend responde en español ("Solo puedes ver tus propias
      // solicitudes"): es copy de producto y se muestra tal cual.
      .catch((err) => setError(err instanceof ApiError ? err.message : MENSAJE_ERROR));
  }, [conCuenta, userId]);

  if (!conCuenta) {
    return <Navigate to={`/registro?volver=${encodeURIComponent(RUTA)}`} replace />;
  }

  const cargando = enviadas === null && recibidas === null && error === null;

  return (
    <div className="mx-auto max-w-3xl space-y-8 p-6 pb-24">
      <header>
        <h1 className="font-display text-3xl text-ink">Mis solicitudes</h1>
        <p className="mt-1 text-sm text-muted">
          Las adopciones que pediste y las que te pidieron a ti. Quien publicó cada mascota es quien
          mueve el estado.
        </p>
      </header>

      {error && (
        <p
          role="alert"
          className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
        >
          {error}
        </p>
      )}

      {cargando && (
        <div role="status" aria-label="Cargando tus solicitudes de adopción" className="space-y-3">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-24 animate-pulse rounded-2xl bg-surface-alt" />
          ))}
        </div>
      )}

      {enviadas !== null && (
        <Seccion
          titulo="Las que enviaste"
          solicitudes={enviadas}
          perspectiva="enviada"
          vacio="Todavía no has pedido ninguna mascota en adopción."
          cta={
            <Link
              to="/adoptar"
              className="mt-4 inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg"
            >
              Ver mascotas en adopción
            </Link>
          }
        />
      )}

      {recibidas !== null && (
        <Seccion
          titulo="Las que recibiste"
          solicitudes={recibidas}
          perspectiva="recibida"
          vacio="Nadie te ha pedido todavía una mascota de las que publicaste."
          cta={
            <Link
              to="/adoptar/publicar"
              className="mt-4 inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg"
            >
              Publicar una mascota
            </Link>
          }
        />
      )}
    </div>
  );
}

/** Una sección con su propio vacío: las dos listas se llenan por caminos
 * distintos (pedir una mascota / publicar una), así que un estado vacío común no
 * podría ofrecer la salida correcta a ninguna de las dos. */
function Seccion({
  titulo,
  solicitudes,
  perspectiva,
  vacio,
  cta,
}: {
  titulo: string;
  solicitudes: Solicitud[];
  perspectiva: 'enviada' | 'recibida';
  vacio: string;
  cta: ReactNode;
}) {
  return (
    <section className="space-y-3">
      <h2 className="font-display text-xl text-ink">{titulo}</h2>
      {solicitudes.length === 0 ? (
        <div className="rounded-2xl border border-line bg-surface p-8 text-center">
          <p className="text-ink-soft">{vacio}</p>
          {cta}
        </div>
      ) : (
        <ListaSolicitudes solicitudes={solicitudes} perspectiva={perspectiva} />
      )}
    </section>
  );
}
