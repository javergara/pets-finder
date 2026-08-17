import { useEffect, useState } from 'react';
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom';
import {
  agendarVisita,
  ApiError,
  aprobarSolicitud,
  descartarSolicitud,
  mediaUrl,
  obtenerSolicitud,
  pedirInformacion,
} from '../api/client';
import type { AccionSolicitud, SolicitudDetalle as SolicitudDetalleTipo } from '../api/types';
import { AvisoSeguridad } from '../components/AvisoSeguridad';
import { HogarResumen } from '../components/HogarResumen';
import { edadLegible, ETIQUETA_ACCION_SOLICITUD, ETIQUETA_ESTADO_SOLICITUD } from '../lib/adopcion';
import {
  mensajeAdopcionAdoptante,
  mensajeAdopcionPublicador,
  urlTelefono,
  urlWhatsApp,
} from '../lib/contacto';
import { getActiveUserId, hasActiveUser } from '../lib/session';
import { tiempoRelativo } from '../lib/tiempo';

// El detalle de una solicitud de adopción (AD-05): con qué se decide y qué se
// puede hacer. La ven las dos partes —quien la envió y quien publicó la
// mascota—, y el backend ya decide qué le toca a cada una.
//
// ⚠️ **Los botones los manda el backend, en `acciones_disponibles`.** Aquí no hay
// ni un array de estados ni una condición sobre `solicitud.estado` para decidir
// qué se puede hacer: el estado solo se usa para *mostrar* (el badge y la
// etiqueta). En `adopta-v1` esta misma pantalla reimplementaba a mano la matriz
// `TRANSICIONES_VALIDAS` del servicio, con listas de estados escritas al lado de
// cada botón y un `.includes(…)` por acción; las dos fuentes de verdad se separan
// a la primera corrección del backend y la UI empieza a ofrecer botones que
// responden 409, o a esconder los que sí valen. Por la misma razón, una acción
// que no llega **no se renderiza**: pintarla deshabilitada "porque el estado no
// la permite" sería la misma duplicación con otra cara.
//
// El guard mecánico de todo esto es un grep sin resultados sobre este archivo:
// ninguna lista literal de estados persistidos puede aparecer aquí —por eso este
// comentario tampoco los nombra entre corchetes—.
//
// ⚠️ **Gate `hasActiveUser()` antes de leer ningún id.** El endpoint exige
// `solicitante_id` y sin cuenta `getActiveUserId()` cae al `DEMO_USER_ID = 1`,
// que en producción es una persona real: un visitante anónimo leería el mensaje,
// el teléfono y el cuestionario de hogar de quien le escribió a esa persona.
// Mismo patrón que `MisSolicitudes` y `MisReportes`.
//
// Aquí **sí** se pinta la afinidad, al revés que en la fila de la lista: es el
// dato con el que se decide y su sitio es este, junto al cuestionario de hogar
// que la produce.
//
// Desde AD-06 (ADR 0013) esta pantalla es además el punto desde el que se
// hablan: no hay chat interno, así que la sección de contacto abre WhatsApp
// hacia el OTRO lado, con el mensaje del estado en el que está la solicitud.
// Quién es "el otro lado" lo decide `contacto()`, aquí abajo.
//
// Paleta `forest`/`ochre`/`muted`: el rojo (`danger`) está reservado en toda la
// app al dominio de emergencia ("perdido") y no entra en el módulo de adopción —
// tampoco en el botón de descartar ni en los avisos de error.

const MENSAJE_ERROR_CARGA =
  'No pudimos cargar esta solicitud. Revisa tu conexión e intenta de nuevo.';
const MENSAJE_ERROR_ACCION = 'No pudimos actualizar la solicitud. Intenta de nuevo.';

/** Qué llama cada botón.
 *
 * `descartar` no está aquí porque no es una llamada directa: abre el formulario
 * del motivo, que el backend exige (422 si llega vacío). El `Exclude` mantiene
 * el mapa exhaustivo — una quinta acción en `AccionSolicitud` no compilaría sin
 * decidir a qué función del cliente llama.
 */
const LLAMADA: Record<
  Exclude<AccionSolicitud, 'descartar'>,
  (solicitudId: number, userId: number) => Promise<SolicitudDetalleTipo>
> = {
  'agendar-visita': agendarVisita,
  'pedir-informacion': pedirInformacion,
  aprobar: aprobarSolicitud,
};

/** A quién se le escribe desde aquí, y con qué texto (AD-06, ADR 0013).
 *
 * ⚠️ **El lado se decide comparando con `adoptante.id`, no con
 * `acciones_disponibles`**: esa lista llega vacía también para quien publicó
 * cuando la solicitud ya está cerrada, y usarla dejaría a esa persona
 * escribiéndose a sí misma. La pantalla solo la abren esos dos (el backend
 * responde 403 a cualquier otro), así que "no soy quien la pidió" es
 * exactamente "soy quien la publicó".
 *
 * Los dos teléfonos vienen de sitios distintos y ninguno es adivinable: el de
 * quien publicó viaja en `publicador` (resuelve el de la mascota o el de la
 * organización) y el de quien la pidió es el que dejó al solicitarla.
 */
function contacto(solicitud: SolicitudDetalleTipo) {
  const soyQuienLaPidio = solicitud.adoptante.id === getActiveUserId();

  if (soyQuienLaPidio) {
    const publicador = solicitud.publicador;
    return {
      nombre: publicador?.nombre ?? 'quien la publicó',
      telefono: publicador?.telefono_contacto ?? null,
      mensaje: mensajeAdopcionAdoptante(solicitud.estado, solicitud.pet.nombre),
      invitacion: `Escríbele para contarle de tu hogar y coordinar lo que sigue con ${solicitud.pet.nombre}.`,
      sinTelefono: 'Todavía no dejó un teléfono de contacto.',
    };
  }

  return {
    nombre: solicitud.adoptante.nombre,
    telefono: solicitud.telefono_contacto,
    mensaje: mensajeAdopcionPublicador(
      solicitud.estado,
      solicitud.pet.nombre,
      solicitud.adoptante.nombre,
    ),
    invitacion: `Escríbele para conocerle y coordinar lo que sigue con ${solicitud.pet.nombre}.`,
    sinTelefono: 'No dejó un teléfono al pedir la mascota.',
  };
}

export function SolicitudDetalle() {
  const { id } = useParams<{ id: string }>();
  // `useParams` devuelve texto: el cliente y el backend hablan de ids numéricos.
  const solicitudId = Number(id);
  const conCuenta = hasActiveUser();
  const [solicitud, setSolicitud] = useState<SolicitudDetalleTipo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [descartando, setDescartando] = useState(false);
  const [motivo, setMotivo] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    // El mismo guard que el `<Navigate>` de abajo: el redirect se renderiza,
    // pero los efectos corren igual después del commit. Sin esto la pantalla
    // pediría los datos con el usuario demo antes de irse.
    if (!conCuenta || !Number.isFinite(solicitudId)) return;
    setError(null);
    // El id del usuario activo se lee DESPUÉS del gate, nunca antes.
    obtenerSolicitud(solicitudId, getActiveUserId())
      .then(setSolicitud)
      // El backend responde en español ("Solo puedes ver tus propias
      // solicitudes"): es copy de producto y se muestra tal cual.
      .catch((err) => setError(err instanceof ApiError ? err.message : MENSAJE_ERROR_CARGA));
  }, [conCuenta, solicitudId]);

  if (!conCuenta) {
    const volver = encodeURIComponent(`/adoptar/solicitud/${id ?? ''}`);
    return <Navigate to={`/registro?volver=${volver}`} replace />;
  }

  if (error) {
    return (
      <div className="mx-auto max-w-2xl space-y-4 p-6 text-center">
        <h1 className="font-display text-2xl text-ink">No pudimos mostrar esta solicitud</h1>
        <p
          role="alert"
          className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
        >
          {error}
        </p>
        <Link
          to="/adoptar/mis-solicitudes"
          className="inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg"
        >
          Ver mis solicitudes
        </Link>
      </div>
    );
  }

  if (!solicitud) {
    return (
      <div
        role="status"
        aria-label="Cargando la solicitud"
        className="mx-auto mt-8 h-96 max-w-2xl animate-pulse rounded-2xl bg-surface-alt"
      />
    );
  }

  const badge = ETIQUETA_ESTADO_SOLICITUD[solicitud.estado];
  const foto = solicitud.pet.fotos[0];
  const acciones = solicitud.acciones_disponibles;
  const otroLado = contacto(solicitud);

  /** Centraliza el loading y el error de las cuatro acciones: cada una devuelve
   * el detalle ya actualizado, así que la pantalla se repinta con la respuesta
   * y no necesita un `GET` detrás de cada botón. */
  async function ejecutarAccion(llamar: () => Promise<SolicitudDetalleTipo>) {
    setErrorAccion(null);
    setEnviando(true);
    try {
      const actualizada = await llamar();
      setSolicitud(actualizada);
      setDescartando(false);
      setMotivo('');
    } catch (err) {
      // El 409 ("Ya no puedes confirmar la adopción: esta solicitud ya está
      // cerrada…") y el 403 llegan con el texto del backend, que desde AD-06 es
      // copy de producto en español y no lleva dentro ningún identificador.
      setErrorAccion(err instanceof ApiError ? err.message : MENSAJE_ERROR_ACCION);
    } finally {
      setEnviando(false);
    }
  }

  function alPulsar(accion: AccionSolicitud) {
    if (accion === 'descartar') {
      setDescartando(true);
      return;
    }
    ejecutarAccion(() => LLAMADA[accion](solicitudId, getActiveUserId()));
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <button type="button" onClick={() => navigate(-1)} className="text-sm text-muted">
        ← Volver
      </button>

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 items-center gap-4">
          <span
            className="h-16 w-16 shrink-0 rounded-xl bg-surface-alt bg-cover bg-center"
            style={{ backgroundImage: foto ? `url(${mediaUrl(foto)})` : undefined }}
          />
          <div className="min-w-0">
            <h1 className="font-display text-2xl text-ink">
              <Link to={`/adoptar/mascota/${solicitud.pet.id}`}>{solicitud.pet.nombre}</Link>
            </h1>
            <p className="text-sm text-muted">
              {[solicitud.pet.raza, edadLegible(solicitud.pet.edad_meses)]
                .filter(Boolean)
                .join(' · ')}
            </p>
            <p className="text-sm text-muted">
              Pedida por {solicitud.adoptante.nombre} · {tiempoRelativo(solicitud.creado_en)}
            </p>
          </div>
        </div>
        <span
          className={`shrink-0 rounded-md px-3 py-1 font-mono text-xs tracking-wide text-bg ${badge.color}`}
        >
          {badge.texto}
        </span>
      </header>

      {/* La `etiqueta` la calcula el backend con los días transcurridos y solo
          aporta cuando dice algo distinto del badge. */}
      {solicitud.etiqueta !== badge.texto && (
        <p className="text-sm text-muted">{solicitud.etiqueta}</p>
      )}

      <section className="rounded-2xl border border-line bg-surface p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-display text-lg text-ink">Su hogar</h2>
          {solicitud.afinidad && (
            <span className="rounded-full bg-forest px-3 py-1 font-mono text-xs text-bg">
              {solicitud.afinidad.score}% afín
            </span>
          )}
        </div>
        {solicitud.home_profile ? (
          <>
            <HogarResumen home={solicitud.home_profile} />
            {solicitud.afinidad && solicitud.afinidad.razones.length > 0 && (
              <ul className="mt-4 space-y-1 border-t border-line-soft pt-4 text-sm text-muted">
                {solicitud.afinidad.razones.map((razon) => (
                  <li key={razon}>· {razon}</li>
                ))}
              </ul>
            )}
          </>
        ) : (
          // Desde AD-04 el cuestionario es opcional: en `adopta-v1` esto era un
          // 404 y la solicitud desaparecía del panel sin ningún error visible.
          <p className="text-ink-soft">
            Todavía no completó el cuestionario de hogar. Puedes preguntarle lo que necesites al
            escribirle.
          </p>
        )}
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-2 font-display text-lg text-ink">Lo que escribió</h2>
        <p className="whitespace-pre-line text-ink-soft">
          {solicitud.mensaje?.trim() || 'No dejó ningún mensaje al pedir la mascota.'}
        </p>
        {solicitud.bio?.trim() && (
          <p className="mt-3 whitespace-pre-line text-sm text-muted">{solicitud.bio}</p>
        )}
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-2 font-display text-lg text-ink">Cómo hablar con {otroLado.nombre}</h2>
        {otroLado.telefono ? (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-ink-soft">{otroLado.invitacion}</p>
            <a
              href={urlWhatsApp(otroLado.telefono, otroLado.mensaje)}
              target="_blank"
              rel="noreferrer"
              className="inline-block self-start rounded-full bg-forest px-5 py-3 font-medium text-bg"
            >
              Escribir por WhatsApp
            </a>
            {/* El número queda visible y marcable: no todo el mundo usa
                WhatsApp, y en una emergencia la llamada gana. */}
            <a href={urlTelefono(otroLado.telefono)} className="self-start font-medium text-forest">
              {otroLado.telefono}
            </a>
            <AvisoSeguridad contexto="contactar" />
          </div>
        ) : (
          // Sin teléfono no se pinta un botón que no lleva a ninguna parte
          // (mismo criterio que `MascotaDetalle`).
          <p className="text-ink-soft">{otroLado.sinTelefono}</p>
        )}
      </section>

      {errorAccion && (
        <p
          role="alert"
          className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
        >
          {errorAccion}
        </p>
      )}

      {/* Solo lo que manda el backend. Sin acciones (el adoptante siempre, y
          quien publica cuando la solicitud ya está cerrada) la sección entera no
          existe: no hay nada que ofrecer ni que explicar apagado. */}
      {acciones.length > 0 && (
        <section
          aria-label="Qué quieres hacer con esta solicitud"
          className="space-y-4 rounded-2xl border border-line bg-surface p-6"
        >
          <h2 className="font-display text-lg text-ink">Qué quieres hacer</h2>
          <div className="flex flex-wrap gap-3">
            {acciones.map((accion) => (
              <button
                key={accion}
                type="button"
                onClick={() => alPulsar(accion)}
                disabled={enviando}
                className={`rounded-full px-4 py-2 font-medium disabled:opacity-40 ${
                  accion === 'aprobar'
                    ? 'bg-forest text-bg'
                    : 'border border-line text-ink-soft bg-surface'
                }`}
              >
                {ETIQUETA_ACCION_SOLICITUD[accion]}
              </button>
            ))}
          </div>

          {descartando && (
            <div className="space-y-3 rounded-xl border border-line bg-surface-alt p-4">
              <label htmlFor="motivo-descarte" className="block text-sm font-medium text-ink-soft">
                Motivo del cierre
              </label>
              {/* Nota interna de quien publica: se guarda, pero no vuelve en
                  ninguna respuesta y quien pidió la mascota no la lee (ADR 0002).
                  Decirlo aquí evita que se escriba pensando que es un mensaje. */}
              <p className="text-xs text-muted">
                Queda como tu nota: quien pidió la mascota no lo va a leer.
              </p>
              <textarea
                id="motivo-descarte"
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                rows={3}
                className="w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
              />
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() =>
                    ejecutarAccion(() =>
                      descartarSolicitud(solicitudId, getActiveUserId(), motivo.trim()),
                    )
                  }
                  // El backend responde 422 con vacío o en blanco: el botón
                  // apagado dice lo mismo antes de gastar el viaje.
                  disabled={motivo.trim().length === 0 || enviando}
                  className="rounded-full bg-ochre px-4 py-2 font-medium text-bg disabled:opacity-40"
                >
                  Confirmar descarte
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setDescartando(false);
                    setMotivo('');
                  }}
                  className="rounded-full border border-line px-4 py-2 font-medium text-ink-soft"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
