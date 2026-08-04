import { useRef, useState } from 'react';
import { mediaUrl } from '../api/client';
import type { Pet } from '../api/types';

const UMBRAL_PX = 110;

interface SwipeCardProps {
  pet: Pet;
  onSwipe: (direccion: 'like' | 'pass') => void;
  onOpenDetail: () => void;
  onToggleFavorito: () => void;
}

export function SwipeCard({ pet, onSwipe, onOpenDetail, onToggleFavorito }: SwipeCardProps) {
  const [dx, setDx] = useState(0);
  const [arrastrando, setArrastrando] = useState(false);
  const inicioX = useRef<number | null>(null);

  const handlePointerDown = (e: React.PointerEvent) => {
    inicioX.current = e.clientX;
    setArrastrando(true);
    (e.target as Element).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (inicioX.current === null) return;
    setDx(e.clientX - inicioX.current);
  };

  const soltar = () => {
    if (Math.abs(dx) > UMBRAL_PX) {
      onSwipe(dx > 0 ? 'like' : 'pass');
    }
    setDx(0);
    setArrastrando(false);
    inicioX.current = null;
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowRight') onSwipe('like');
    if (e.key === 'ArrowLeft') onSwipe('pass');
    if (e.key === 'Enter') onOpenDetail();
  };

  const opacidadSello = Math.min(Math.abs(dx) / UMBRAL_PX, 1);
  const foto = pet.fotos[0] ? mediaUrl(pet.fotos[0]) : undefined;

  return (
    <div
      role="group"
      aria-label={`Ficha de ${pet.nombre}, deslizar a la derecha para me interesa, a la izquierda para ahora no`}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={soltar}
      onPointerCancel={soltar}
      style={{
        transform: `translateX(${dx}px) rotate(${dx / 22}deg)`,
        transition: arrastrando ? 'none' : 'transform .28s cubic-bezier(.2,.8,.3,1)',
      }}
      className="relative flex h-140 w-full max-w-105 cursor-grab touch-none flex-col overflow-hidden rounded-[22px] border border-line bg-surface shadow-[0_18px_40px_-28px_rgba(27,26,23,.5)] select-none"
    >
      <div
        className="pointer-events-none absolute top-5 right-5 z-10 rounded-md bg-forest px-3 py-1 font-mono text-xs tracking-wide text-bg"
        style={{ opacity: dx > 0 ? opacidadSello : 0, transform: 'rotate(-8deg)' }}
      >
        Me interesa
      </div>
      <div
        className="pointer-events-none absolute top-5 left-5 z-10 rounded-md bg-ochre px-3 py-1 font-mono text-xs tracking-wide text-bg"
        style={{ opacity: dx < 0 ? opacidadSello : 0, transform: 'rotate(8deg)' }}
      >
        Ahora no
      </div>

      <div
        className="flex-1 bg-surface-alt bg-cover bg-center"
        style={{ backgroundImage: foto ? `url(${foto})` : undefined }}
      >
        <div className="flex h-full items-start gap-2 p-4">
          {pet.afinidad && (
            <span className="rounded-full bg-forest px-3 py-1 font-mono text-xs text-bg">
              {pet.afinidad.score}% afín
            </span>
          )}
          <button
            type="button"
            aria-label={pet.es_favorito ? 'Quitar de favoritos' : 'Guardar en favoritos'}
            onPointerDown={(e) => e.stopPropagation()}
            onClick={onToggleFavorito}
            className={`ml-auto flex h-9 w-9 items-center justify-center rounded-full bg-surface/90 text-xl ${
              pet.es_favorito ? 'text-forest' : 'text-muted'
            }`}
          >
            {pet.es_favorito ? '♥' : '♡'}
          </button>
        </div>
      </div>

      <div className="border-t border-line p-4">
        <h3 className="font-display text-2xl text-ink">{pet.nombre}</h3>
        <p className="text-sm text-muted">
          {Math.round(pet.edad_meses / 12)} años · {pet.raza}
        </p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {pet.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="rounded-full bg-forest-tint px-2.5 py-1 text-xs text-forest">
              {tag}
            </span>
          ))}
        </div>
        <div className="mt-3 flex items-center justify-between border-t border-line-soft pt-3">
          <span className="text-xs text-muted">{pet.shelter?.nombre}</span>
          <button
            type="button"
            onClick={onOpenDetail}
            className="text-sm font-medium text-forest hover:text-forest-hover"
          >
            Ver ficha
          </button>
        </div>
      </div>
    </div>
  );
}
