import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { desmarcarFavorito, listarFavoritos, mediaUrl } from '../api/client';
import type { Pet } from '../api/types';
import { getActiveUserId } from '../lib/session';

export function Favoritos() {
  const [favoritos, setFavoritos] = useState<Pet[] | null>(null);

  useEffect(() => {
    listarFavoritos(getActiveUserId()).then(setFavoritos);
  }, []);

  if (favoritos === null) {
    return (
      <div className="mx-auto mt-8 grid max-w-4xl grid-cols-2 gap-4 p-6 sm:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-56 animate-pulse rounded-2xl bg-surface-alt" />
        ))}
      </div>
    );
  }

  if (favoritos.length === 0) {
    return (
      <div className="mx-auto max-w-md p-8 text-center">
        <h1 className="font-display text-2xl text-ink">Aún no tienes favoritos</h1>
        <p className="mt-2 text-muted">
          Guarda las mascotas que te interesen para revisarlas después, sin comprometerte a nada
          todavía.
        </p>
        <Link to="/descubrir" className="mt-4 inline-block font-medium text-forest">
          Ir a Descubrir →
        </Link>
      </div>
    );
  }

  async function quitar(e: React.MouseEvent, petId: number) {
    e.preventDefault();
    e.stopPropagation();
    await desmarcarFavorito(getActiveUserId(), petId);
    setFavoritos((prev) => (prev ? prev.filter((pet) => pet.id !== petId) : prev));
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-6 font-display text-3xl text-ink">Favoritos</h1>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {favoritos.map((pet) => (
          <div key={pet.id} className="rounded-2xl border border-line bg-surface p-3">
            <Link to={`/mascota/${pet.id}`}>
              {pet.fotos[0] && (
                <img
                  src={mediaUrl(pet.fotos[0])}
                  alt={`Foto de ${pet.nombre}`}
                  className="aspect-4/3 w-full rounded-xl object-cover"
                />
              )}
              <div className="mt-2 flex items-center justify-between">
                <p className="font-display text-lg text-ink">{pet.nombre}</p>
                {pet.afinidad && (
                  <span className="rounded-full bg-forest px-2 py-0.5 font-mono text-xs text-bg">
                    {pet.afinidad.score}%
                  </span>
                )}
              </div>
              <p className="text-sm text-muted">{Math.round(pet.edad_meses / 12)} años</p>
            </Link>
            <button
              type="button"
              onClick={(e) => quitar(e, pet.id)}
              className="mt-2 block w-full text-center text-sm font-medium text-ochre"
            >
              Quitar de favoritos
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
