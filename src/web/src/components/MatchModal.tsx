import { mediaUrl } from '../api/client';
import type { Pet } from '../api/types';

interface MatchModalProps {
  pet: Pet;
  onSeguirViendo: () => void;
  onVerMatches: () => void;
}

export function MatchModal({ pet, onSeguirViendo, onVerMatches }: MatchModalProps) {
  const foto = pet.fotos[0] ? mediaUrl(pet.fotos[0]) : undefined;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Nuevo match con ${pet.nombre}`}
      className="fixed inset-0 z-20 flex items-center justify-center bg-[rgba(27,26,23,.42)] p-6"
    >
      <div className="w-full max-w-105 rounded-2xl border border-line bg-surface p-8 text-center [animation:popIn_.24s_cubic-bezier(.2,.8,.3,1)]">
        <p className="font-mono text-xs tracking-wide text-muted-2 uppercase">Nuevo match</p>
        {foto && (
          <img
            src={foto}
            alt={`Foto de ${pet.nombre}`}
            className="mx-auto mt-4 h-28 w-28 rounded-full object-cover"
          />
        )}
        <h2 className="mt-4 font-display text-2xl text-ink">Te interesa {pet.nombre}</h2>
        <p className="mt-2 text-sm text-ink-soft">
          Enviamos tu perfil y tu cuestionario de hogar a {pet.shelter?.nombre ?? 'el refugio'}.
          Suelen responder en {pet.shelter?.tiempo_respuesta_horas ?? 24} horas.
        </p>
        <div className="mt-6 flex flex-col gap-2">
          <button
            type="button"
            onClick={onVerMatches}
            className="rounded-lg bg-forest px-4 py-3 font-medium text-bg hover:bg-forest-hover"
          >
            Ver mis matches
          </button>
          <button
            type="button"
            onClick={onSeguirViendo}
            className="rounded-lg px-4 py-3 font-medium text-muted hover:text-ink"
          >
            Seguir viendo perfiles
          </button>
        </div>
      </div>
    </div>
  );
}
