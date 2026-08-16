import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { ApiError, desmarcarFavorita, listarFavoritas } from '../api/client';
import type { Mascota } from '../api/types';
import { MascotaCard } from '../components/MascotaCard';
import { getActiveUserId, hasActiveUser } from '../lib/session';

// La lista guardada (AD-07): las mascotas que alguien marcó con el corazón desde
// el catálogo, el deck o la ficha. Es la otra mitad de la función — sin una
// pantalla donde volver a verlas, guardar sería un gesto que no lleva a nada.
//
// ⚠️ **Gate de cuenta antes de leer ningún id**, igual que `MisSolicitudes` y por
// la misma razón: esta pantalla no compara autoría, *consulta* por el id activo,
// y sin cuenta `getActiveUserId()` cae al `DEMO_USER_ID = 1`, que en producción
// es una persona real. Un visitante anónimo vería las mascotas guardadas de esa
// persona —un historial de navegación con su nombre encima— y al tocar un
// corazón se las borraría. Por eso el `if (!conCuenta) return` vive **también
// dentro del efecto**: el `<Navigate>` se renderiza, pero los efectos corren
// igual después del commit, así que un gate que solo esté en el render no impide
// que la petición salga.
//
// Reusa `MascotaCard` en vez de una rejilla propia (lo que hacía `Favoritos.tsx`
// en `adopta-v1`): una sola tarjeta significa un solo sitio donde arreglar el
// corazón, el lazy de la foto o el link a la ficha. Aquí el corazón siempre nace
// lleno —todo lo que llega está guardado por definición— y tocarlo quita.
//
// Sin filtros ni paginación a propósito: una lista de favoritos son decenas de
// mascotas elegidas a mano, no un catálogo; el orden lo fija el backend (lo
// último guardado primero) y es el que la persona recuerda.

const MENSAJE_ERROR =
  'No pudimos cargar tus mascotas guardadas. Revisa tu conexión e intenta de nuevo.';

/** La ruta propia, para el `?volver=` del registro: quien se registra desde aquí
 * vuelve aquí. Se llama `mis-favoritas` y no `favoritas` por consistencia con
 * `/adoptar/mis-solicitudes` y `/mis-reportes` — el prefijo "mis" es lo que
 * distingue en toda la app lo propio de lo público. */
const RUTA = '/adoptar/mis-favoritas';

export function MisFavoritas() {
  const conCuenta = hasActiveUser();
  const userId = getActiveUserId();
  const [mascotas, setMascotas] = useState<Mascota[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!conCuenta) return;
    setError(null);
    listarFavoritas(userId)
      .then(setMascotas)
      // Sin este `.catch` un fallo de red deja el esqueleto girando para
      // siempre y la pantalla parece colgada (bug real de este repo, arreglado
      // en `81d45ee` para otras tres pantallas). El backend responde en español
      // ("Solo puedes ver tus propios favoritos"): es copy de producto y se
      // muestra tal cual.
      .catch((err) => setError(err instanceof ApiError ? err.message : MENSAJE_ERROR));
  }, [conCuenta, userId]);

  if (!conCuenta) {
    return <Navigate to={`/registro?volver=${encodeURIComponent(RUTA)}`} replace />;
  }

  /** Quita la mascota de la lista, en optimista. */
  function quitar(mascota: Mascota) {
    // La tarjeta se va entera, no se queda con el corazón vacío: en ESTA
    // pantalla una mascota sin guardar ya no pertenece a lo que se está
    // mirando, y dejarla ahí obligaría a recargar para saber qué quedó.
    setMascotas((previas) => (previas ? previas.filter((m) => m.id !== mascota.id) : previas));

    desmarcarFavorita(userId, mascota.id).catch(() => {
      // Vacío A PROPÓSITO, no por descuido (`docs/conventions.md` §3, mismo
      // criterio que el corazón del catálogo). Y **la tarjeta no se repone**:
      // reponer lo que alguien acaba de quitar es peor que perder el registro
      // —vería reaparecer sola una mascota que decidió sacar de su lista—, y lo
      // que se pierde entretanto es una fila en una lista privada que la
      // próxima carga vuelve a mostrar para quitarla otra vez.
    });
  }

  const cargando = mascotas === null && error === null;

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6 pb-24">
      <header>
        <h1 className="font-display text-3xl text-ink">Mis favoritas</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          Las mascotas que guardaste para pensarlo con calma. Guardar no avisa a nadie ni aparta a
          la mascota: cuando te decidas, pídela en su ficha.
        </p>
      </header>

      {error && (
        <p
          role="alert"
          className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
        >
          {error}
        </p>
      )}

      {cargando && (
        <div
          role="status"
          aria-label="Cargando tus mascotas guardadas"
          className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
        >
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-80 animate-pulse rounded-[22px] bg-surface-alt" />
          ))}
        </div>
      )}

      {mascotas !== null &&
        (mascotas.length === 0 ? (
          <div className="rounded-2xl border border-line bg-surface p-10 text-center">
            <p className="text-ink-soft">
              Todavía no has guardado ninguna mascota. Toca el corazón de la que te llame la
              atención y la encuentras aquí.
            </p>
            {/* Al deck y no al catálogo: quien llega a su lista vacía no
                necesita otra rejilla igual a la que ya vio, necesita empezar a
                elegir de una en una. */}
            <Link
              to="/adoptar/descubrir"
              className="mt-4 inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg"
            >
              Descubrir mascotas
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {mascotas.map((mascota) => (
              <MascotaCard
                key={mascota.id}
                mascota={mascota}
                onAlternarFavorita={() => quitar(mascota)}
              />
            ))}
          </div>
        ))}
    </div>
  );
}
