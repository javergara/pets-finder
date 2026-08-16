import { useRef, useState } from 'react';
import { mediaUrl } from '../api/client';
import type { DireccionSwipe, Mascota } from '../api/types';
import {
  ETIQUETA_SEXO,
  ETIQUETA_TAMANO_MASCOTA,
  edadLegible,
  tituloMascota,
} from '../lib/adopcion';

// Tarjeta del deck de descubrimiento (AD-03), port de `SwipeCard` de la era
// Adopta con la piel visual de `MascotaCard` (foto sin recorte, chips redondos,
// pie separado por una línea suave).
//
// **Tres rutas equivalentes, no alternativas**: los botones, el teclado
// (`ArrowRight`/`ArrowLeft`/`Enter` sobre el `role="group"`) y el gesto hacen
// exactamente lo mismo. El gesto es la gracia del deck, pero quien no puede
// arrastrar —teclado, lector de pantalla, motricidad reducida— tiene que poder
// adoptar igual; por eso los botones no son un extra "por si acaso" y llevan sus
// tres tests propios.
//
// Copy: **"Me interesa" / "Ahora no", nunca "rechazar"**. El match no es mutuo
// (ADR 0002): un `pass` no rechaza a nadie, solo saca esa tarjeta de este deck.
// Paleta `forest`/`ochre`; `danger` está reservado en toda la app a "perdido".
//
// La transición inline la neutraliza el `@media (prefers-reduced-motion: reduce)`
// de `index.css`, que ya baja cualquier `transition-duration` con `!important`.
// Por eso aquí no hay ningún `!important` que se lo pise.

/** Cuánto hay que arrastrar para que cuente como decisión. Por debajo, la
 * tarjeta vuelve a su sitio: el roce accidental no saca a nadie del deck. */
const UMBRAL_PX = 110;

/** Con más de tres chips la fila salta de línea y a 360px empuja el pie de la
 * tarjeta fuera de la pantalla (mismo tope que `MascotaCard`). */
const MAX_TAGS = 3;

/** Las razones se muestran completas hasta tres: el acceptance pide al menos
 * dos, y `_razones()` del backend devuelve siempre tres o más. */
const MAX_RAZONES = 3;

type Props = {
  mascota: Mascota;
  onSwipe: (direccion: DireccionSwipe) => void;
  onAbrirFicha: () => void;
  /** Opcional a propósito: el corazón solo se pinta si alguien lo escucha. Los
   * favoritos son de AD-07, así que hasta entonces la pantalla no manda esta
   * prop y no queda en producción un botón que no guarda nada. */
  onAlternarFavorita?: () => void;
};

export function MascotaSwipeCard({ mascota, onSwipe, onAbrirFicha, onAlternarFavorita }: Props) {
  const [dx, setDx] = useState(0);
  const [arrastrando, setArrastrando] = useState(false);
  const inicioX = useRef<number | null>(null);

  const reposar = () => {
    setDx(0);
    setArrastrando(false);
    inicioX.current = null;
  };

  const alPresionar = (e: React.PointerEvent) => {
    inicioX.current = e.clientX;
    setArrastrando(true);
    // ⚠️ Defensivo y sobre `currentTarget`, no sobre `target`: `target` puede ser
    // un hijo (la foto, un chip) y capturarle el puntero a él deja el arrastre a
    // medias. `setPointerCapture` **no existe en jsdom** (medido: `typeof` da
    // `undefined`), así que sin el `?.` cada `pointerdown` de los tests lanza un
    // `TypeError` que React reporta por consola; y en cualquier entorno donde el
    // método falte, la excepción abortaría lo que viniera después en el handler.
    // Va al final y con guarda: si no se puede capturar el puntero, el arrastre
    // igual funciona.
    const el = e.currentTarget as Element & { setPointerCapture?: (id: number) => void };
    el.setPointerCapture?.(e.pointerId);
  };

  const alMover = (e: React.PointerEvent) => {
    if (inicioX.current === null) return;
    setDx(e.clientX - inicioX.current);
  };

  const alSoltar = () => {
    if (Math.abs(dx) > UMBRAL_PX) onSwipe(dx > 0 ? 'like' : 'pass');
    reposar();
  };

  // `pointercancel` es el navegador llevándose el gesto (un scroll que gana, una
  // llamada entrante), no la persona soltando: se descarta entero. `adopta-v1`
  // lo mandaba al mismo handler que `pointerup` y un gesto abortado sacaba la
  // carta del deck sin vuelta atrás.
  const alCancelar = () => reposar();

  const alTeclear = (e: React.KeyboardEvent) => {
    // Solo cuando el foco está en la tarjeta misma. Sin esto, el Enter que
    // activa "Me interesa" burbujearía hasta aquí y abriría además la ficha:
    // un swipe y una navegación con una sola tecla.
    if (e.target !== e.currentTarget) return;
    if (e.key === 'ArrowRight') onSwipe('like');
    if (e.key === 'ArrowLeft') onSwipe('pass');
    if (e.key === 'Enter') onAbrirFicha();
  };

  const titulo = tituloMascota(mascota);
  const foto = mascota.fotos[0];
  const lugar = mascota.zona === 'Otro' ? mascota.ciudad_texto ?? 'Colombia' : mascota.zona;
  const edadYRaza = [edadLegible(mascota.edad_meses), mascota.raza].filter(Boolean).join(' · ');
  const opacidadSello = Math.min(Math.abs(dx) / UMBRAL_PX, 1);
  const razones = mascota.afinidad?.razones.slice(0, MAX_RAZONES) ?? [];

  return (
    <div
      role="group"
      aria-label={`Ficha de ${titulo}. Deslizá a la derecha si te interesa, a la izquierda para dejarla pasar.`}
      tabIndex={0}
      onKeyDown={alTeclear}
      onPointerDown={alPresionar}
      onPointerMove={alMover}
      onPointerUp={alSoltar}
      onPointerCancel={alCancelar}
      style={{
        transform: `translateX(${dx}px) rotate(${dx / 22}deg)`,
        transition: arrastrando ? 'none' : 'transform .28s cubic-bezier(.2,.8,.3,1)',
      }}
      className="relative flex w-full max-w-105 cursor-grab touch-none flex-col overflow-hidden rounded-[22px] border border-line bg-surface shadow-[0_18px_40px_-28px_rgba(27,26,23,.5)] select-none"
    >
      {/* Sellos del gesto: decorativos y duplicados de los botones, así que se
          ocultan al lector de pantalla en vez de leerse dos veces. */}
      <span
        aria-hidden
        className="pointer-events-none absolute top-5 right-5 z-10 rounded-md bg-forest px-3 py-1 font-mono text-xs tracking-wide text-bg"
        style={{ opacity: dx > 0 ? opacidadSello : 0, transform: 'rotate(-8deg)' }}
      >
        Me interesa
      </span>
      <span
        aria-hidden
        className="pointer-events-none absolute top-5 left-5 z-10 rounded-md bg-ochre px-3 py-1 font-mono text-xs tracking-wide text-bg"
        style={{ opacity: dx < 0 ? opacidadSello : 0, transform: 'rotate(8deg)' }}
      >
        Ahora no
      </span>

      <div className="relative aspect-4/3 bg-surface-alt">
        {foto ? (
          <img
            src={mediaUrl(foto)}
            alt={`Foto de ${titulo}, en adopción`}
            draggable={false}
            className="absolute inset-0 h-full w-full object-contain"
          />
        ) : (
          <span className="absolute inset-0 flex items-center justify-center text-sm text-muted">
            Sin foto todavía
          </span>
        )}
        <div className="relative flex items-start gap-2 p-3">
          {mascota.afinidad && (
            <span className="rounded-full bg-forest px-3 py-1 font-mono text-xs text-bg">
              {mascota.afinidad.score}% afín
            </span>
          )}
          {onAlternarFavorita && (
            <button
              type="button"
              aria-label={mascota.es_favorito ? 'Quitar de favoritos' : 'Guardar en favoritos'}
              // Sin esto, empezar el gesto sobre el corazón arrastra la tarjeta:
              // quien solo quería guardar la mascota se la lleva del deck.
              onPointerDown={(e) => e.stopPropagation()}
              onClick={onAlternarFavorita}
              className={`ml-auto flex h-9 w-9 items-center justify-center rounded-full bg-surface/90 text-xl ${
                mascota.es_favorito ? 'text-forest' : 'text-muted'
              }`}
            >
              {mascota.es_favorito ? '♥' : '♡'}
            </button>
          )}
        </div>
      </div>

      <div className="border-t border-line p-4">
        <h3 className="font-display text-2xl text-ink">{titulo}</h3>
        <p className="text-sm text-forest">{edadYRaza}</p>

        {razones.length > 0 && (
          <ul className="mt-2 space-y-1 text-sm text-muted">
            {razones.map((razon) => (
              <li key={razon}>· {razon}</li>
            ))}
          </ul>
        )}

        {mascota.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {mascota.tags.slice(0, MAX_TAGS).map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-forest-tint px-2.5 py-1 text-xs text-forest"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        <div className="mt-3 flex items-center justify-between gap-2 border-t border-line-soft pt-3 text-xs text-muted">
          <span>{lugar}</span>
          {mascota.publicador && <span>{mascota.publicador.nombre}</span>}
          <span>
            {ETIQUETA_SEXO[mascota.sexo]} · {ETIQUETA_TAMANO_MASCOTA[mascota.tamano]}
          </span>
        </div>

        {/* Las tres acciones, en el mismo orden que el gesto: izquierda pasa,
            derecha interesa. */}
        <div className="mt-4 flex items-center justify-between gap-2">
          <button
            type="button"
            aria-label="Ahora no"
            onClick={() => onSwipe('pass')}
            className="rounded-full border border-line bg-surface px-4 py-2 text-sm font-medium text-ochre"
          >
            Ahora no
          </button>
          <button
            type="button"
            aria-label="Ver ficha"
            onClick={onAbrirFicha}
            className="text-sm font-medium text-forest underline-offset-4 hover:underline"
          >
            Ver ficha
          </button>
          <button
            type="button"
            aria-label="Me interesa"
            onClick={() => onSwipe('like')}
            className="rounded-full bg-forest px-4 py-2 text-sm font-medium text-bg"
          >
            Me interesa
          </button>
        </div>
      </div>
    </div>
  );
}
