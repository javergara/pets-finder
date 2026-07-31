import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listarMascotas, registrarSwipe } from '../api/client';
import type { Pet } from '../api/types';
import { MatchModal } from '../components/MatchModal';
import { SwipeCard } from '../components/SwipeCard';
import { DEMO_USER_ID } from '../lib/constants';

export function Descubrir() {
  const [mascotas, setMascotas] = useState<Pet[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [matchPet, setMatchPet] = useState<Pet | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    listarMascotas(DEMO_USER_ID)
      .then(setMascotas)
      .catch(() => setError('No pudimos cargar las mascotas. Intenta de nuevo en un momento.'));
  }, []);

  const actual = mascotas?.[0];

  async function handleSwipe(direccion: 'like' | 'pass') {
    if (!actual) return;
    setMascotas((prev) => (prev ? prev.slice(1) : prev));
    try {
      const swipe = await registrarSwipe(DEMO_USER_ID, actual.id, direccion);
      if (swipe.match) setMatchPet(actual);
    } catch {
      // El swipe nunca se bloquea por un error de red (docs/conventions.md §3);
      // ya se quitó la tarjeta de la baraja localmente.
    }
  }

  if (error) {
    return <p className="p-8 text-center text-danger">{error}</p>;
  }

  if (mascotas === null) {
    return (
      <div className="mx-auto mt-8 h-140 w-full max-w-105 animate-pulse rounded-[22px] bg-surface-alt" />
    );
  }

  return (
    <div className="mx-auto flex max-w-105 flex-col items-center p-6">
      <h1 className="mb-6 font-display text-3xl text-ink">Descubrir</h1>

      {actual ? (
        <div className="relative w-full">
          <div className="absolute inset-x-3 top-3 h-140 scale-97 rounded-[22px] border border-line bg-surface-alt" />
          <div className="absolute inset-x-6 top-6 h-140 scale-94 rounded-[22px] border border-line bg-surface-alt" />
          <SwipeCard
            key={actual.id}
            pet={actual}
            onSwipe={handleSwipe}
            onOpenDetail={() => navigate(`/mascota/${actual.id}`)}
          />
        </div>
      ) : (
        <div className="rounded-2xl border border-line bg-surface p-8 text-center">
          <p className="text-ink-soft">No hay más perfiles por ahora.</p>
          <p className="mt-2 text-sm text-muted">
            Prueba ampliando el radio o quitando filtros más tarde.
          </p>
        </div>
      )}

      {actual && (
        <div className="mt-6 flex items-center gap-6">
          <button
            type="button"
            aria-label="Ahora no"
            onClick={() => handleSwipe('pass')}
            className="flex h-14 w-14 items-center justify-center rounded-full border border-line bg-surface text-xl text-ochre"
          >
            ✕
          </button>
          <button
            type="button"
            aria-label="Ver ficha"
            onClick={() => navigate(`/mascota/${actual.id}`)}
            className="flex h-11.5 w-11.5 items-center justify-center rounded-full border border-line bg-surface text-forest"
          >
            i
          </button>
          <button
            type="button"
            aria-label="Me interesa"
            onClick={() => handleSwipe('like')}
            className="flex h-14 w-14 items-center justify-center rounded-full bg-forest text-xl text-bg"
          >
            ♥
          </button>
        </div>
      )}

      {matchPet && (
        <MatchModal
          pet={matchPet}
          onSeguirViendo={() => setMatchPet(null)}
          onVerMatches={() => navigate('/matches')}
        />
      )}
    </div>
  );
}
