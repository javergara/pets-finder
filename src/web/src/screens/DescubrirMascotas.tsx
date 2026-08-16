import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { type FiltrosMascotas, listarDeck, registrarSwipe } from '../api/client';
import type { DireccionSwipe, Mascota } from '../api/types';
import { FiltrosAdopcion } from '../components/FiltrosAdopcion';
import { MascotaSwipeCard } from '../components/MascotaSwipeCard';
import { FILTROS_ADOPCION_DEFAULT } from '../lib/adopcion';
import { getActiveUserId, hasActiveUser } from '../lib/session';

// Deck de descubrimiento (AD-03), port de `Descubrir` de la era Adopta. Una
// mascota a la vez, tres formas de decidir (botones, teclado y gesto: las pone la
// tarjeta) y la siguiente lista al instante.
//
// ⚠️ **Toda lectura del usuario pasa por `hasActiveUser()`.** `getActiveUserId()`
// cae al `DEMO_USER_ID = 1`, que en producción es una persona real: registrar un
// swipe sin cuenta lo grabaría a su nombre y le ensuciaría su propio deck (el bug
// de autoría del fix `cc4de85`). Por eso, sin cuenta, "Me interesa" manda al
// registro y "Ahora no" solo pasa de carta, en local, sin tocar la API.
//
// **Ver el deck no exige cuenta ni perfil de hogar.** `listarDeck()` sin
// `adoptante_id` responde 200: no excluye lo ya swipeado y viene sin afinidad. Y
// no se porta el `RequiereHomeProfile` de adopta-v1: un cuestionario obligatorio
// antes de mirar contradice la cuenta liviana del ADR 0005 y es justo la fricción
// que este producto no puede permitirse en una emergencia. Lo que queda es una
// invitación no bloqueante.
//
// **La carta se quita en optimista y no vuelve**: un fallo de `registrarSwipe` se
// traga en silencio (`docs/conventions.md` §3) y no repone la mascota ni dispara
// un refetch. Reponer la carta que alguien acaba de pasar es peor que perder el
// registro de ese swipe.
//
// Paleta: aquí solo hay `forest` y `ochre`. El rojo de emergencia está reservado
// en toda la app a "perdido" y no entra en este módulo, ni siquiera en el error
// de carga, que se pinta con el borde neutro de las tarjetas (misma regla que
// `MascotaDetalle`; el nombre del token vive en `ETIQUETA_ESTADO_MASCOTA`).

const MENSAJE_ERROR =
  'No pudimos cargar las mascotas para descubrir. Revisa tu conexión e intenta de nuevo.';

/** La ruta propia, para el `?volver=` del registro: quien se registra desde el
 * deck vuelve al deck, no a la landing. */
const RUTA = '/adoptar/descubrir';

export function DescubrirMascotas() {
  const [filtros, setFiltros] = useState<FiltrosMascotas>(FILTROS_ADOPCION_DEFAULT);
  const [mascotas, setMascotas] = useState<Mascota[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Cada cambio de filtro pide un deck nuevo. Solo aquí: los swipes no
  // re-consultan (ver cabecera).
  useEffect(() => {
    setError(null);
    listarDeck(hasActiveUser() ? getActiveUserId() : undefined, filtros)
      .then(setMascotas)
      .catch(() => setError(MENSAJE_ERROR));
  }, [filtros]);

  const actual = mascotas?.[0];
  const cargando = mascotas === null && error === null;
  // Sin perfil de hogar el backend devuelve el deck entero con `afinidad: null`;
  // basta mirar la carta de arriba para saber en cuál de los dos mundos estamos.
  const sinAfinidad = actual !== undefined && actual.afinidad === null;

  async function decidir(direccion: DireccionSwipe) {
    if (!actual) return;
    const conCuenta = hasActiveUser();

    // "Me interesa" es el único que necesita saber quién eres: es el que en AD-05
    // se convierte en una solicitud con tu contacto. Se pide la cuenta ANTES de
    // gastar la carta, para no perderla en el camino al registro.
    if (direccion === 'like' && !conCuenta) {
      navigate(`/registro?volver=${encodeURIComponent(RUTA)}`);
      return;
    }

    setMascotas((previas) => (previas ? previas.slice(1) : previas));

    // Sin cuenta, "Ahora no" es una preferencia de esta sesión y nada más: se
    // pasa de carta en local. Mandarlo al backend lo guardaría como swipe del
    // usuario 1.
    if (!conCuenta) return;

    try {
      await registrarSwipe(getActiveUserId(), actual.id, direccion);
    } catch {
      // A propósito en silencio: la decisión ya se tomó en pantalla y el deck no
      // se bloquea por la red (`docs/conventions.md` §3). Lo que se pierde es el
      // registro de un swipe, no la mascota — sigue en el catálogo.
    }
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 p-6 pb-24 lg:flex-row lg:items-start">
      {/* En móvil los filtros van arriba y apilados (nada de columnas ni anchos
          fijos): a 360px cualquier fila lateral empuja la tarjeta fuera de la
          pantalla. En escritorio pasan a ser una columna pegajosa. */}
      <aside className="w-full lg:sticky lg:top-6 lg:w-72 lg:shrink-0">
        <FiltrosAdopcion
          filtros={filtros}
          onChange={setFiltros}
          onReset={() => setFiltros(FILTROS_ADOPCION_DEFAULT)}
        />
      </aside>

      <div className="mx-auto flex w-full max-w-105 flex-col items-center">
        <header className="mb-4 w-full text-center">
          <h1 className="font-display text-3xl text-ink">Descubrir</h1>
          <p className="mt-1 text-sm text-muted">
            Una por una: deslízala a la derecha si te interesa, a la izquierda si no es el momento.
          </p>
        </header>

        {error && (
          <p
            role="alert"
            className="w-full rounded-2xl border border-line bg-surface p-4 text-center text-sm text-ink-soft"
          >
            {error}
          </p>
        )}

        {cargando && (
          <div
            role="status"
            aria-label="Cargando mascotas para descubrir"
            className="h-140 w-full animate-pulse rounded-[22px] bg-surface-alt"
          />
        )}

        {actual && (
          <MascotaSwipeCard
            // La `key` reinicia el arrastre de la tarjeta al cambiar de mascota:
            // sin ella la nueva heredaría el desplazamiento de la anterior.
            key={actual.id}
            mascota={actual}
            onSwipe={decidir}
            onAbrirFicha={() => navigate(`/adoptar/mascota/${actual.id}`)}
            // `onAlternarFavorita` NO se pasa: los favoritos son de AD-07 y un
            // corazón que no guarda nada es peor que ningún corazón.
          />
        )}

        {mascotas !== null && mascotas.length === 0 && (
          <div className="w-full rounded-2xl border border-line bg-surface p-8 text-center">
            <p className="text-ink-soft">
              No quedan mascotas por ver con estos filtros. Vuelve más tarde: cada día se publican
              rescates nuevos.
            </p>
            <Link
              to="/adoptar"
              className="mt-4 inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg"
            >
              Ver el catálogo completo
            </Link>
          </div>
        )}

        {sinAfinidad && (
          /* Invitación, no guard: el deck ya está funcionando debajo, y quien no
             quiera contestar sigue viendo todas las mascotas (AD-03). Desde
             AD-04 sí lleva enlace: la ruta existe y sin él habría que adivinar
             la URL para poder contestar. */
          <section className="mt-6 w-full rounded-2xl border border-forest-tint-line bg-forest-tint p-4 text-center">
            <h2 className="font-display text-lg text-forest">Mejora tus coincidencias</h2>
            <p className="mt-1 text-sm text-ink-soft">
              Cuéntanos cómo es tu casa y tu rutina y te mostramos primero las mascotas que mejor
              encajan contigo, con el porqué de cada una.
            </p>
            <Link
              to="/adoptar/mi-hogar"
              className="mt-3 inline-block rounded-full bg-forest px-5 py-2.5 font-medium text-bg"
            >
              Contestar seis preguntas
            </Link>
          </section>
        )}
      </div>
    </div>
  );
}
