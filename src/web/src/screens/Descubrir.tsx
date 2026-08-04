import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { desmarcarFavorito, listarMascotas, marcarFavorito, registrarSwipe } from '../api/client';
import { FILTROS_DEFAULT, type Filtros, type Pet } from '../api/types';
import { FiltrosPanel } from '../components/FiltrosPanel';
import { MatchModal } from '../components/MatchModal';
import { SwipeCard } from '../components/SwipeCard';
import { getActiveUserId } from '../lib/session';

export function Descubrir() {
  const [mascotas, setMascotas] = useState<Pet[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [matchPet, setMatchPet] = useState<Pet | null>(null);
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_DEFAULT);
  const navigate = useNavigate();

  useEffect(() => {
    listarMascotas(getActiveUserId(), filtros)
      .then(setMascotas)
      .catch(() => setError('No pudimos cargar las mascotas. Intenta de nuevo en un momento.'));
  }, [filtros]);

  const actual = mascotas?.[0];

  async function handleSwipe(direccion: 'like' | 'pass') {
    if (!actual) return;
    setMascotas((prev) => (prev ? prev.slice(1) : prev));
    try {
      const swipe = await registrarSwipe(getActiveUserId(), actual.id, direccion);
      if (swipe.match) setMatchPet(actual);
    } catch {
      // El swipe nunca se bloquea por un error de red (docs/conventions.md §3);
      // ya se quitó la tarjeta de la baraja localmente.
    }
  }

  async function handleToggleFavorito(petId: number) {
    const mascota = mascotas?.find((m) => m.id === petId);
    if (!mascota) return;
    const nuevoValor = !mascota.es_favorito;
    setMascotas((prev) =>
      prev ? prev.map((m) => (m.id === petId ? { ...m, es_favorito: nuevoValor } : m)) : prev,
    );
    try {
      if (nuevoValor) {
        await marcarFavorito(getActiveUserId(), petId);
      } else {
        await desmarcarFavorito(getActiveUserId(), petId);
      }
    } catch {
      // Igual que el swipe (docs/conventions.md §3): la acción optimista no se
      // revierte por un error de red; el toggle no debe bloquear la navegación.
    }
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 p-6 lg:flex-row lg:items-start lg:justify-center">
      <aside className="w-full lg:sticky lg:top-6 lg:w-72 lg:shrink-0">
        <FiltrosPanel
          filtros={filtros}
          onChange={setFiltros}
          onReset={() => setFiltros(FILTROS_DEFAULT)}
        />
      </aside>

      <div className="mx-auto flex w-full max-w-105 flex-col items-center">
        <h1 className="mb-2 font-display text-3xl text-ink">Descubrir</h1>
        {mascotas !== null && (
          <p className="mb-4 text-sm text-muted">{mascotas.length} perfiles cerca de ti</p>
        )}

        {error ? (
          <p className="p-8 text-center text-danger">{error}</p>
        ) : mascotas === null ? (
          <div className="mt-2 h-140 w-full animate-pulse rounded-[22px] bg-surface-alt" />
        ) : (
          <>
            {actual ? (
              <div className="relative w-full">
                <div className="absolute inset-x-3 top-3 h-140 scale-97 rounded-[22px] border border-line bg-surface-alt" />
                <div className="absolute inset-x-6 top-6 h-140 scale-94 rounded-[22px] border border-line bg-surface-alt" />
                <SwipeCard
                  key={actual.id}
                  pet={actual}
                  onSwipe={handleSwipe}
                  onOpenDetail={() => navigate(`/mascota/${actual.id}`)}
                  onToggleFavorito={() => handleToggleFavorito(actual.id)}
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
          </>
        )}

        {matchPet && (
          <MatchModal
            pet={matchPet}
            onSeguirViendo={() => setMatchPet(null)}
            onVerMatches={() => navigate('/matches')}
          />
        )}
      </div>
    </div>
  );
}
