import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ApiError, editarMascota, listarMascotas, listarSolicitudes } from '../api/client';
import type { EstadoMascota, Mascota, Solicitud } from '../api/types';
import { ETIQUETA_ESTADO_MASCOTA, tituloMascota } from '../lib/adopcion';
import { getActiveUserId } from '../lib/session';
import { ListaSolicitudes } from './ListaSolicitudes';
import { MascotaCard } from './MascotaCard';

// Las mascotas que una organización tiene en adopción, dentro de su ficha
// (AD-02, A1). Vive aquí y no en `OrganizacionDetalle` porque esa pantalla
// acaba de bajar de 533 a 181 líneas: la pestaña le cuesta una veintena de
// líneas y todo el contenido —carga, resumen, rejilla y las acciones del
// autor— es de este componente.
//
// ⚠️ `esAutor` es la única puerta de escritura, igual que en
// `SeccionNecesidades` y `AdministrarOrganizacion`: cualquiera ve la rejilla
// (es información pública, la misma de /adoptar), pero solo quien registró el
// lugar publica o cambia el estado. El backend lo vuelve a verificar con un
// 403; esto es la mitad de UI del mismo trato.
//
// Paleta `forest`/`ochre`: `danger` está reservado en toda la app a "perdido" y
// no entra en el módulo de adopción, tampoco en los bloques de error.

type Props = {
  organizacionId: number;
  nombreOrganizacion: string;
  telefonoContacto: string;
  zona: string;
  esAutor: boolean;
};

const MENSAJE_ERROR_CARGA =
  'No pudimos cargar las mascotas en adopción de este lugar. Revisa tu conexión e intenta de nuevo.';
const MENSAJE_ERROR_ESTADO = 'No pudimos cambiar el estado. Intenta de nuevo.';
const MENSAJE_ERROR_SOLICITUDES =
  'No pudimos cargar las solicitudes de este lugar. Revisa tu conexión e intenta de nuevo.';

// Mismo orden que el catálogo: disponible → en proceso → adoptado.
const ESTADOS = Object.keys(ETIQUETA_ESTADO_MASCOTA) as EstadoMascota[];

export function PanelAdopcionOrganizacion({
  organizacionId,
  nombreOrganizacion,
  telefonoContacto,
  zona,
  esAutor,
}: Props) {
  const [mascotas, setMascotas] = useState<Mascota[] | null>(null);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [errorEstado, setErrorEstado] = useState<string | null>(null);
  const [guardando, setGuardando] = useState<number | null>(null);
  const [solicitudes, setSolicitudes] = useState<Solicitud[] | null>(null);
  const [errorSolicitudes, setErrorSolicitudes] = useState<string | null>(null);

  useEffect(() => {
    setErrorCarga(null);
    // `estado: 'todos'` a propósito: en su propia ficha el lugar también quiere
    // ver las adoptadas (son su mejor carta) y las que están en proceso, que el
    // catálogo público esconde.
    listarMascotas({ organizacionId, estado: 'todos' })
      .then(setMascotas)
      // El backend responde en español ("La organización 7 no existe"): copy de
      // producto, se muestra tal cual.
      .catch((err) => setErrorCarga(err instanceof ApiError ? err.message : MENSAJE_ERROR_CARGA));
  }, [organizacionId]);

  // Las solicitudes que recibió el lugar (AD-05). **Solo si `esAutor`**, y no
  // basta con esconderlas: la respuesta trae el nombre de quien pidió cada
  // mascota, así que pedirlas ya sería exponer datos de terceros a cualquier
  // visitante de la ficha. El backend lo vuelve a verificar con un 403; esto es
  // la mitad de UI del mismo trato, igual que el resto del panel.
  //
  // `organizacionId` y no `publicadorId`: aquí se responde como el lugar. El
  // filtro de publicador traería además las mascotas que esa persona publicó a
  // título propio, que no son de esta ficha (esas se ven en /adoptar/mis-solicitudes).
  useEffect(() => {
    if (!esAutor) return;
    setErrorSolicitudes(null);
    listarSolicitudes({ organizacionId })
      .then(setSolicitudes)
      .catch((err) =>
        setErrorSolicitudes(err instanceof ApiError ? err.message : MENSAJE_ERROR_SOLICITUDES),
      );
  }, [esAutor, organizacionId]);

  async function cambiarEstado(mascotaId: number, estado: EstadoMascota) {
    setErrorEstado(null);
    setGuardando(mascotaId);
    try {
      const actualizada = await editarMascota(mascotaId, { user_id: getActiveUserId(), estado });
      setMascotas((previas) => (previas ?? []).map((m) => (m.id === mascotaId ? actualizada : m)));
    } catch (err) {
      // Un 403 (o cualquier fallo) avisa y deja el panel como estaba: la lista no
      // se toca, así que el selector vuelve solo al estado que el backend sí tiene.
      setErrorEstado(err instanceof ApiError ? err.message : MENSAJE_ERROR_ESTADO);
    } finally {
      setGuardando(null);
    }
  }

  const conteos = [
    ['Disponibles', mascotas?.filter((m) => m.estado === 'disponible').length ?? 0],
    ['En proceso', mascotas?.filter((m) => m.estado === 'en_proceso').length ?? 0],
    ['Adoptadas', mascotas?.filter((m) => m.estado === 'adoptado').length ?? 0],
  ] as const;

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-xl text-ink">Mascotas en adopción</h2>
          <p className="mt-1 max-w-xl text-sm text-muted">
            Animales que {nombreOrganizacion} tiene listos para una familia en {zona}.
            {esAutor && ` Quien se interese escribirá al ${telefonoContacto}.`}
          </p>
        </div>
        {esAutor && (
          <Link
            to={`/adoptar/publicar?organizacion=${organizacionId}`}
            className="shrink-0 rounded-full bg-forest px-5 py-2 text-sm font-medium text-bg"
          >
            Publicar una mascota
          </Link>
        )}
      </div>

      {errorCarga && (
        <p
          role="alert"
          className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
        >
          {errorCarga}
        </p>
      )}

      {mascotas === null && errorCarga === null && (
        <div
          role="status"
          aria-label="Cargando las mascotas en adopción del lugar"
          className="grid grid-cols-1 gap-5 sm:grid-cols-2"
        >
          {[1, 2].map((n) => (
            <div key={n} className="h-80 animate-pulse rounded-[22px] bg-surface-alt" />
          ))}
        </div>
      )}

      {mascotas !== null && mascotas.length > 0 && (
        <>
          <dl
            aria-label="Resumen de las mascotas del lugar"
            className="grid grid-cols-3 gap-3 rounded-2xl border border-line bg-surface p-4 text-center"
          >
            {conteos.map(([etiqueta, total]) => (
              <div key={etiqueta}>
                <dt className="text-xs text-muted">{etiqueta}</dt>
                <dd className="font-display text-2xl text-forest">{total}</dd>
              </div>
            ))}
          </dl>

          {errorEstado && (
            <p
              role="alert"
              className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
            >
              {errorEstado}
            </p>
          )}

          <ul className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            {mascotas.map((mascota) => (
              <li key={mascota.id} className="flex flex-col gap-2">
                <MascotaCard mascota={mascota} />
                {/* El selector va FUERA de la tarjeta: `MascotaCard` es un enlace
                    entero a la ficha y un select dentro de un enlace no se puede
                    usar con teclado. */}
                {/* La ficha pública no ofrece editar las mascotas de un lugar
                    (no sabe quién lo registró), así que este es el camino del
                    autor para corregirlas. */}
                {esAutor && (
                  <Link
                    to={`/adoptar/mascota/${mascota.id}/editar`}
                    aria-label={`Editar la ficha de ${tituloMascota(mascota)}`}
                    className="self-start text-sm font-medium text-forest underline underline-offset-4"
                  >
                    Editar
                  </Link>
                )}
                {esAutor && (
                  <select
                    aria-label={`Estado de ${tituloMascota(mascota)}`}
                    value={mascota.estado}
                    disabled={guardando === mascota.id}
                    onChange={(e) => cambiarEstado(mascota.id, e.target.value as EstadoMascota)}
                    className="rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink disabled:opacity-60"
                  >
                    {ESTADOS.map((estado) => (
                      <option key={estado} value={estado}>
                        {ETIQUETA_ESTADO_MASCOTA[estado].texto}
                      </option>
                    ))}
                  </select>
                )}
              </li>
            ))}
          </ul>
        </>
      )}

      {mascotas !== null && mascotas.length === 0 && (
        <p className="rounded-2xl border border-line bg-surface p-6 text-sm text-ink-soft">
          {nombreOrganizacion} todavía no tiene mascotas publicadas en adopción.
          {esAutor
            ? ' Si rescataron una que ya nadie reclamó, publícala aquí: quien la busque la verá en el catálogo.'
            : ' Si buscas adoptar, mira el resto del catálogo mientras tanto.'}
        </p>
      )}

      {/* Las solicitudes van al final y solo para el autor: la rejilla de arriba
          es lo que vino a ver cualquiera, y esto es su bandeja de entrada.
          Mientras cargan no se pinta nada —ni siquiera el título— para no dejar
          un encabezado suelto sobre un hueco; un fallo aquí no toca la rejilla,
          que es información pública y sigue en pie. */}
      {esAutor && (solicitudes !== null || errorSolicitudes !== null) && (
        <div className="space-y-3 border-t border-line pt-4">
          <h3 className="font-display text-lg text-ink">Solicitudes recibidas</h3>
          {errorSolicitudes && (
            <p
              role="alert"
              className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
            >
              {errorSolicitudes}
            </p>
          )}
          {solicitudes !== null &&
            (solicitudes.length > 0 ? (
              <ListaSolicitudes solicitudes={solicitudes} perspectiva="recibida" />
            ) : (
              <p className="rounded-2xl border border-line bg-surface p-6 text-sm text-ink-soft">
                Nadie ha pedido todavía una de estas mascotas. Cuando alguien lo haga, aparecerá
                aquí con su cuestionario de hogar.
              </p>
            ))}
        </div>
      )}
    </section>
  );
}
