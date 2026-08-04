import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  agendarVisita,
  ApiError,
  descartarSolicitud,
  obtenerSolicitud,
  pedirInformacion,
} from '../api/client';
import type { SolicitudDetalle as SolicitudDetalleType } from '../api/types';
import { HogarResumen } from '../components/HogarResumen';
import { DEMO_SHELTER_ID } from '../lib/constants';

// Estados terminales de una solicitud: ninguna acción del refugio es válida sobre
// ellos (services/solicitudes.py::TRANSICIONES_VALIDAS nunca los incluye).
const ESTADOS_TERMINALES = ['adoptado', 'cerrado'];

export function SolicitudDetalle() {
  const { matchId } = useParams<{ matchId: string }>();
  const [solicitud, setSolicitud] = useState<SolicitudDetalleType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [mostrandoFormularioDescarte, setMostrandoFormularioDescarte] = useState(false);
  const [motivoDescarte, setMotivoDescarte] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (!matchId) return;
    obtenerSolicitud(DEMO_SHELTER_ID, Number(matchId)).then(setSolicitud);
  }, [matchId]);

  if (!solicitud) {
    return <div className="mx-auto mt-8 h-80 max-w-2xl animate-pulse rounded-2xl bg-surface-alt" />;
  }

  // Deben replicar EXACTAMENTE la matriz `TRANSICIONES_VALIDAS` del backend
  // (src/api/adopta_api/services/solicitudes.py).
  const permiteAgendar = ['solicitado', 'en_revision'].includes(solicitud.estado);
  const permitePedirInfo = solicitud.estado === 'solicitado';
  const permiteDescartar = ['solicitado', 'en_revision', 'visita_agendada'].includes(
    solicitud.estado,
  );
  const esTerminal = ESTADOS_TERMINALES.includes(solicitud.estado);

  async function ejecutarAccion(accion: () => Promise<SolicitudDetalleType>) {
    setError(null);
    setEnviando(true);
    try {
      const resultado = await accion();
      setSolicitud(resultado);
      setMostrandoFormularioDescarte(false);
      setMotivoDescarte('');
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'No pudimos actualizar la solicitud. Intenta de nuevo.',
      );
    } finally {
      setEnviando(false);
    }
  }

  function handleAgendarVisita() {
    ejecutarAccion(() => agendarVisita(DEMO_SHELTER_ID, Number(matchId)));
  }

  function handlePedirInformacion() {
    ejecutarAccion(() => pedirInformacion(DEMO_SHELTER_ID, Number(matchId)));
  }

  function handleConfirmarDescarte() {
    ejecutarAccion(() =>
      descartarSolicitud(DEMO_SHELTER_ID, Number(matchId), motivoDescarte.trim()),
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <button type="button" onClick={() => navigate(-1)} className="text-sm text-muted">
        ← Volver
      </button>

      <header className="flex items-center justify-between gap-4 rounded-2xl border border-line bg-surface p-6">
        <div>
          <h1 className="font-display text-2xl text-ink">{solicitud.adoptante.nombre}</h1>
          <p className="text-sm text-muted">
            Solicitud para {solicitud.pet.nombre} · {solicitud.etiqueta}
          </p>
          <Link
            to={`/refugio/solicitudes/${matchId}/mensajes`}
            className="mt-1 inline-block text-sm font-medium text-forest"
          >
            Ver conversación
          </Link>
        </div>
        <span className="rounded-full bg-forest px-3 py-1 font-mono text-sm text-bg">
          {solicitud.afinidad.score}% afín
        </span>
      </header>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-4 font-display text-lg text-ink">Cuestionario de hogar</h2>
        <HogarResumen home={solicitud.home_profile} />
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-2 font-display text-lg text-ink">Sobre mí</h2>
        <p className="text-ink-soft">
          {solicitud.bio && solicitud.bio.trim().length > 0
            ? solicitud.bio
            : 'Todavía no escribió nada sobre sí. Esto lo ven los refugios al recibir su solicitud.'}
        </p>
      </section>

      {error && (
        <p className="rounded-2xl border border-danger/40 bg-danger/10 p-4 text-sm text-danger">
          {error}
        </p>
      )}

      {esTerminal ? (
        <p className="rounded-2xl border border-line bg-surface-alt p-4 text-sm text-muted">
          {solicitud.etiqueta}
        </p>
      ) : (
        <section className="space-y-4 rounded-2xl border border-line bg-surface p-6">
          <h2 className="font-display text-lg text-ink">Acciones</h2>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleAgendarVisita}
              disabled={!permiteAgendar || enviando}
              className="rounded-full bg-forest px-4 py-2 font-medium text-bg disabled:opacity-40"
            >
              Agendar visita
            </button>
            <button
              type="button"
              onClick={handlePedirInformacion}
              disabled={!permitePedirInfo || enviando}
              className="rounded-full border border-line px-4 py-2 font-medium text-ink disabled:opacity-40"
            >
              Pedir más información
            </button>
            <button
              type="button"
              onClick={() => setMostrandoFormularioDescarte(true)}
              disabled={!permiteDescartar || enviando}
              className="rounded-full border border-danger px-4 py-2 font-medium text-danger disabled:opacity-40"
            >
              Descartar
            </button>
          </div>

          {mostrandoFormularioDescarte && (
            <div className="space-y-3 rounded-xl border border-line bg-surface-alt p-4">
              <label htmlFor="motivo-descarte" className="text-sm font-medium text-ink-soft">
                Motivo del descarte
              </label>
              <textarea
                id="motivo-descarte"
                value={motivoDescarte}
                onChange={(e) => setMotivoDescarte(e.target.value)}
                rows={3}
                className="w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
              />
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleConfirmarDescarte}
                  disabled={motivoDescarte.trim().length === 0 || enviando}
                  className="rounded-full bg-danger px-4 py-2 font-medium text-bg disabled:opacity-40"
                >
                  Confirmar descarte
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMostrandoFormularioDescarte(false);
                    setMotivoDescarte('');
                  }}
                  className="rounded-full border border-line px-4 py-2 font-medium text-ink"
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
