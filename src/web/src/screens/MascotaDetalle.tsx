import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { mediaUrl, obtenerMascota, registrarSwipe } from '../api/client';
import type { Pet } from '../api/types';
import { getActiveUserId } from '../lib/session';

export function MascotaDetalle() {
  const { id } = useParams<{ id: string }>();
  const [pet, setPet] = useState<Pet | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    obtenerMascota(Number(id), getActiveUserId()).then(setPet);
  }, [id]);

  if (!pet) {
    return <div className="mx-auto mt-8 h-80 max-w-2xl animate-pulse rounded-2xl bg-surface-alt" />;
  }

  async function meInteresa() {
    if (!pet) return;
    await registrarSwipe(getActiveUserId(), pet.id, 'like');
    navigate('/matches');
  }

  const foto = pet.fotos[0] ? mediaUrl(pet.fotos[0]) : undefined;

  return (
    <div className="mx-auto max-w-2xl p-6 pb-24">
      <button type="button" onClick={() => navigate(-1)} className="mb-4 text-sm text-muted">
        ← Volver
      </button>

      {foto && (
        <img
          src={foto}
          alt={`Foto de ${pet.nombre}`}
          className="aspect-4/3 w-full rounded-2xl border border-line object-cover"
        />
      )}

      <div className="mt-4 flex items-start justify-between">
        <div>
          <h1 className="font-display text-3xl text-ink">{pet.nombre}</h1>
          <p className="text-muted">
            {Math.round(pet.edad_meses / 12)} años · {pet.raza}
          </p>
        </div>
        {pet.afinidad && (
          <span className="rounded-full bg-forest px-3 py-1 font-mono text-sm text-bg">
            {pet.afinidad.score}% afín
          </span>
        )}
      </div>

      {pet.afinidad && (
        <p className="mt-3 rounded-xl border border-forest-tint-line bg-forest-tint p-4 text-sm text-forest">
          {pet.afinidad.explicacion}
        </p>
      )}

      <div className="mt-2 flex flex-wrap gap-1.5">
        {pet.tags.map((tag) => (
          <span key={tag} className="rounded-full bg-forest-tint px-2.5 py-1 text-xs text-forest">
            {tag}
          </span>
        ))}
      </div>

      <section className="mt-6">
        <h2 className="font-mono text-xs tracking-wide text-muted-2 uppercase">Su historia</h2>
        <p className="mt-2 text-ink-soft">{pet.historia}</p>
      </section>

      <section className="mt-6">
        <h2 className="font-mono text-xs tracking-wide text-muted-2 uppercase">Salud y cuidados</h2>
        <ul className="mt-2 grid grid-cols-2 gap-2 text-sm text-ink-soft">
          <li>{pet.esterilizado ? '✓' : '—'} Esterilizado</li>
          <li>{pet.vacunas_al_dia ? '✓' : '—'} Vacunas al día</li>
          <li>{pet.microchip ? '✓' : '—'} Microchip</li>
          <li>{pet.desparasitado ? '✓' : '—'} Desparasitado</li>
        </ul>
      </section>

      {pet.shelter && (
        <section className="mt-6 rounded-xl border border-line p-4">
          <p className="font-medium text-ink">{pet.shelter.nombre}</p>
          <p className="text-sm text-muted">
            {pet.shelter.verificado ? 'Refugio verificado' : 'Refugio'} ·{' '}
            {pet.shelter.adopciones_cerradas} adopciones cerradas · responde en{' '}
            {pet.shelter.tiempo_respuesta_horas}h
          </p>
        </section>
      )}

      <div className="fixed inset-x-0 bottom-0 flex gap-3 border-t border-line bg-surface p-4">
        <button
          type="button"
          onClick={() => navigate('/descubrir')}
          className="flex h-14 w-14 items-center justify-center rounded-full border border-line text-xl text-ochre"
          aria-label="Ahora no"
        >
          ✕
        </button>
        <button
          type="button"
          onClick={meInteresa}
          className="flex-1 rounded-full bg-forest font-medium text-bg"
        >
          Me interesa adoptar
        </button>
      </div>
    </div>
  );
}
