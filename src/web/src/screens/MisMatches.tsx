import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listarMatches, mediaUrl } from '../api/client';
import type { MatchWithPet } from '../api/types';
import { getActiveUserId } from '../lib/session';

const ESTADO_COPY: Record<string, { texto: string; clase: string }> = {
  solicitado: { texto: '● Esperando refugio', clase: 'text-ochre' },
  en_revision: { texto: '● En revisión', clase: 'text-ochre' },
  visita_agendada: { texto: '● Visita agendada', clase: 'text-forest' },
  adoptado: { texto: '● Adopción cerrada', clase: 'text-forest' },
  cerrado: { texto: '● Solicitud cerrada', clase: 'text-muted' },
};

export function MisMatches() {
  const [matches, setMatches] = useState<MatchWithPet[] | null>(null);

  useEffect(() => {
    listarMatches(getActiveUserId()).then(setMatches);
  }, []);

  if (matches === null) {
    return (
      <div className="mx-auto mt-8 grid max-w-4xl grid-cols-2 gap-4 p-6 sm:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-56 animate-pulse rounded-2xl bg-surface-alt" />
        ))}
      </div>
    );
  }

  if (matches.length === 0) {
    return (
      <div className="mx-auto max-w-md p-8 text-center">
        <h1 className="font-display text-2xl text-ink">Aún no tienes matches</h1>
        <p className="mt-2 text-muted">
          Cuando te interese una mascota, aparecerá aquí de inmediato.
        </p>
        <Link to="/descubrir" className="mt-4 inline-block font-medium text-forest">
          Ir a Descubrir →
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-6 font-display text-3xl text-ink">Mis matches</h1>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {matches.map((match) => {
          const copy = ESTADO_COPY[match.estado] ?? ESTADO_COPY.solicitado;
          return (
            <Link
              key={match.id}
              to={`/mascota/${match.pet.id}`}
              className="rounded-2xl border border-line bg-surface p-3"
            >
              {match.pet.fotos[0] && (
                <img
                  src={mediaUrl(match.pet.fotos[0])}
                  alt={`Foto de ${match.pet.nombre}`}
                  className="aspect-4/3 w-full rounded-xl object-cover"
                />
              )}
              <div className="mt-2 flex items-center justify-between">
                <span className="rounded-full bg-forest px-2 py-0.5 font-mono text-xs text-bg">
                  {match.afinidad.score}%
                </span>
                <span className={`text-xs ${copy.clase}`}>{copy.texto}</span>
              </div>
              <p className="mt-1 font-display text-lg text-ink">{match.pet.nombre}</p>
              <p className="text-sm text-muted">{Math.round(match.pet.edad_meses / 12)} años</p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
