import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  type FiltrosMascotas,
  listarMascotas,
  mediaUrl,
  obtenerAdopcionesResumen,
} from '../api/client';
import type { AdopcionesResumen, Mascota } from '../api/types';
import { FiltrosAdopcion } from '../components/FiltrosAdopcion';
import { MascotaCard } from '../components/MascotaCard';
import { FILTROS_ADOPCION_DEFAULT } from '../lib/adopcion';

// Catálogo público de mascotas en adopción (AD-01).
//
// ⚠️ Pantalla de SOLO LECTURA. No lleva ninguna acción que escriba —ni favorito ni
// solicitud— y por eso no llama a `getActiveUserId()`: esa función cae al usuario
// demo (id 1) cuando no hay cuenta, así que un visitante sin registrarse crearía
// datos a nombre de otra persona real en producción. Mirar quién necesita hogar
// nunca exige cuenta; las acciones que escriben llegan con su gate en AD-05/AD-07.
//
// Tampoco manda `adoptante_id` al backend: en AD-01 no cambiaría la respuesta
// (afinidad, favorito y solicitud viajan siempre vacíos) y mandar un id inventado
// sería justo el bug de privacidad que el módulo evita por convención.
//
// Sin paginación a propósito: `listarMascotas` devuelve el listado completo, como
// `listarOrganizaciones` en /ayudar. Cuando el catálogo crezca se copia el paginado
// de `listarReportesPaginado` (header `X-Total-Count`) sin tocar nada más.

const MENSAJE_ERROR =
  'No pudimos cargar las mascotas en adopción. Revisa tu conexión e intenta de nuevo.';

export function CatalogoAdopcion() {
  const [filtros, setFiltros] = useState<FiltrosMascotas>(FILTROS_ADOPCION_DEFAULT);
  const [mascotas, setMascotas] = useState<Mascota[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adopciones, setAdopciones] = useState<AdopcionesResumen | null>(null);

  // Métrica de esperanza del módulo, como la franja de reencuentros de la landing:
  // si falla, simplemente no aparece — nunca bloquea el catálogo.
  useEffect(() => {
    obtenerAdopcionesResumen()
      .then(setAdopciones)
      .catch(() => setAdopciones(null));
  }, []);

  // Cada cambio de filtro re-consulta. Las tarjetas anteriores se quedan en
  // pantalla mientras llega la respuesta (mismo criterio que /reportes): la
  // rejilla no parpadea y el esqueleto solo se ve en la primera carga.
  useEffect(() => {
    setError(null);
    listarMascotas(filtros)
      .then(setMascotas)
      .catch(() => setError(MENSAJE_ERROR));
  }, [filtros]);

  const cargando = mascotas === null && error === null;
  const hayFiltros =
    filtros.especie.length > 0 ||
    filtros.tamano.length > 0 ||
    filtros.energia.length > 0 ||
    filtros.zona !== '';

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6 pb-24">
      <header className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="font-display text-3xl text-ink">Mascotas en adopción</h1>
            <p className="mt-1 max-w-2xl text-sm text-muted">
              Animales rescatados que ya nadie reclamó y esperan una familia. Los publican
              fundaciones, veterinarias y rescatistas de la comunidad.
              {mascotas && mascotas.length > 0 && (
                <span className="mt-0.5 block">
                  <strong className="text-forest">
                    {mascotas.length === 1
                      ? '1 mascota busca hogar'
                      : `${mascotas.length} mascotas buscan hogar`}
                  </strong>
                  {hayFiltros && ' con estos filtros'}
                </span>
              )}
            </p>
          </div>
          {/* Dos entradas, ningún gate: mirar el catálogo o el deck nunca pide
              cuenta (la del deck vive en su "Me interesa", AD-03). "Descubrir" va
              con estilo secundario porque el catálogo entero ya está debajo. */}
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <Link
              to="/adoptar/descubrir"
              className="rounded-full border border-line bg-surface px-5 py-2 text-sm font-medium text-forest"
            >
              Descubrir una por una
            </Link>
            <Link
              to="/adoptar/publicar"
              className="rounded-full bg-forest px-5 py-2 text-sm font-medium text-bg"
            >
              Dar en adopción
            </Link>
          </div>
        </div>
        <FiltrosAdopcion
          filtros={filtros}
          onChange={setFiltros}
          onReset={() => setFiltros(FILTROS_ADOPCION_DEFAULT)}
        />
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
          aria-label="Cargando mascotas en adopción"
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
            {hayFiltros ? (
              <>
                <p className="text-ink-soft">Ninguna mascota coincide con estos filtros.</p>
                <button
                  type="button"
                  onClick={() => setFiltros(FILTROS_ADOPCION_DEFAULT)}
                  className="mt-4 rounded-full bg-forest px-5 py-2 font-medium text-bg"
                >
                  Ver todas las mascotas
                </button>
              </>
            ) : (
              <>
                <p className="text-ink-soft">
                  Todavía no hay mascotas publicadas en adopción. Si rescataste una y busca familia,
                  la primera puede ser la tuya.
                </p>
                <Link
                  to="/adoptar/publicar"
                  className="mt-4 inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg"
                >
                  Publicar una mascota en adopción
                </Link>
                <p className="mt-3 text-sm text-muted">
                  ¿Buscas una fundación o una veterinaria?{' '}
                  <Link to="/ayudar" className="font-medium text-forest underline">
                    Ver los centros de ayuda
                  </Link>
                </p>
              </>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {mascotas.map((mascota) => (
              <MascotaCard key={mascota.id} mascota={mascota} />
            ))}
          </div>
        ))}

      {adopciones !== null && adopciones.total > 0 && (
        <section className="rounded-2xl border border-forest-tint-line bg-forest-tint p-6 text-center">
          <p className="font-display text-3xl text-forest">{adopciones.total}</p>
          <p className="text-sm text-ink-soft">
            {adopciones.total === 1 ? 'adopción lograda' : 'adopciones logradas'} gracias a la
            comunidad
          </p>
          <div className="mt-4 flex justify-center gap-3">
            {adopciones.recientes.slice(0, 4).map((adoptada) => (
              <div
                key={adoptada.id}
                aria-label={`${adoptada.nombre}, ya tiene hogar`}
                className="h-14 w-14 rounded-xl border border-forest-tint-line bg-surface-alt bg-cover bg-center"
                style={{
                  backgroundImage: adoptada.fotos[0]
                    ? `url(${mediaUrl(adoptada.fotos[0])})`
                    : undefined,
                }}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
