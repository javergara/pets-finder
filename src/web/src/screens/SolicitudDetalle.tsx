import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { obtenerSolicitud } from '../api/client';
import type { SolicitudDetalle as SolicitudDetalleType } from '../api/types';
import { HogarResumen } from '../components/HogarResumen';
import { DEMO_SHELTER_ID } from '../lib/constants';

export function SolicitudDetalle() {
  const { matchId } = useParams<{ matchId: string }>();
  const [solicitud, setSolicitud] = useState<SolicitudDetalleType | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!matchId) return;
    obtenerSolicitud(DEMO_SHELTER_ID, Number(matchId)).then(setSolicitud);
  }, [matchId]);

  if (!solicitud) {
    return <div className="mx-auto mt-8 h-80 max-w-2xl animate-pulse rounded-2xl bg-surface-alt" />;
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

      <p className="rounded-2xl border border-line bg-surface-alt p-4 text-sm text-muted">
        Agendar visita, pedir más información y descartar con motivo estarán disponibles en una
        próxima entrega.
      </p>
    </div>
  );
}
