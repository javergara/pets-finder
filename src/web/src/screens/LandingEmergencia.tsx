import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { mediaUrl, obtenerConteos, obtenerReunidos } from '../api/client';
import type { Conteos, ReunidosResumen } from '../api/types';
import { SLUGS_ZONA } from '../lib/ciudades';

// Landing de emergencia: dos caminos gigantes, decididos en dos segundos,
// y la franja de reencuentros como métrica de esperanza.
export function LandingEmergencia() {
  const [reunidos, setReunidos] = useState<ReunidosResumen | null>(null);
  const [conteos, setConteos] = useState<Conteos | null>(null);

  useEffect(() => {
    // La landing nunca se bloquea por estas llamadas: sin datos, no aparecen.
    obtenerReunidos()
      .then(setReunidos)
      .catch(() => setReunidos(null));
    obtenerConteos()
      .then(setConteos)
      .catch(() => setConteos(null));
  }, []);

  return (
    <div className="mx-auto flex min-h-svh max-w-4xl flex-col items-center justify-center gap-8 p-6 text-center">
      <img src="/logo.svg" alt="Pet Finder Col" className="h-9 w-auto sm:h-11" />
      <p className="font-mono text-sm uppercase tracking-wider text-muted">
        Colombia · Sismo del 10 de agosto de 2026
      </p>
      <h1 className="max-w-2xl font-display text-5xl text-ink sm:text-6xl">
        Ayudemos a cada mascota a volver a casa.
      </h1>
      <p className="max-w-xl text-lg text-ink-soft">
        Reporta una mascota perdida o una que encontraste entre los escombros. La comunidad busca
        contigo: cada reporte con foto y ubicación acerca un reencuentro.
      </p>

      <div className="flex w-full max-w-2xl flex-col gap-4 sm:flex-row">
        <Link
          to="/reportar/perdido"
          className="flex-1 rounded-2xl bg-danger px-8 py-6 text-xl font-medium text-bg shadow-sm"
        >
          Perdí a mi mascota
        </Link>
        <Link
          to="/reportar/encontrado"
          className="flex-1 rounded-2xl bg-forest px-8 py-6 text-xl font-medium text-bg shadow-sm"
        >
          Encontré una mascota
        </Link>
      </div>

      {/* La dimensión del problema en vivo (feature 34): prueba social y urgencia. */}
      {conteos && conteos.perdidos + conteos.encontrados > 0 && (
        <p className="text-sm text-muted">
          Ahora mismo la comunidad busca a{' '}
          <strong className="text-danger">{conteos.perdidos} mascotas perdidas</strong> y cuida{' '}
          <strong className="text-forest">{conteos.encontrados} encontradas</strong>.
        </p>
      )}

      {/* Accesos secundarios: botones con borde, visibles a primera vista pero
          sin competir con los dos CTAs llenos de arriba. */}
      <div className="flex w-full max-w-2xl flex-col items-center gap-3">
        <Link
          to="/buscar"
          className="w-full rounded-xl border-2 border-forest px-6 py-3 text-base font-medium text-forest"
        >
          🔎 Busca a tu mascota por descripción
        </Link>
        <div className="flex w-full flex-col gap-3 sm:flex-row">
          <Link
            to="/reportes"
            className="flex-1 rounded-xl border-2 border-forest px-6 py-3 text-base font-medium text-forest"
          >
            Ver todos los reportes
          </Link>
          <Link
            to="/mapa"
            className="flex-1 rounded-xl border-2 border-forest px-6 py-3 text-base font-medium text-forest"
          >
            Ver el mapa
          </Link>
        </div>
        <Link
          to="/ayudar"
          className="text-sm font-medium text-forest underline-offset-4 hover:underline"
        >
          Centros de ayuda: acopio, fundaciones y donaciones
        </Link>
      </div>

      {reunidos !== null && reunidos.total > 0 && (
        <section className="w-full max-w-2xl rounded-2xl border border-forest-tint-line bg-forest-tint p-6">
          <p className="font-display text-3xl text-forest">{reunidos.total}</p>
          <p className="text-sm text-ink-soft">
            {reunidos.total === 1 ? 'reencuentro logrado' : 'reencuentros logrados'} gracias a la
            comunidad
          </p>
          <Link
            to="/reportes?estado=reunido"
            className="mt-2 inline-block text-sm font-medium text-forest underline-offset-4 hover:underline"
          >
            Ver todos los reencuentros
          </Link>
          <div className="mt-4 flex justify-center gap-3">
            {reunidos.recientes.slice(0, 4).map((reporte) => (
              <Link
                key={reporte.id}
                to={`/reporte/${reporte.id}`}
                aria-label={`Reencuentro de ${reporte.nombre_mascota ?? reporte.especie}`}
                className="h-14 w-14 rounded-xl border border-forest-tint-line bg-surface-alt bg-cover bg-center"
                style={{
                  backgroundImage: reporte.foto_url
                    ? `url(${mediaUrl(reporte.foto_url)})`
                    : undefined,
                }}
              />
            ))}
          </div>
        </section>
      )}

      <p className="max-w-md text-xs text-muted">
        {/* Cada ciudad enlaza su landing con SEO propio (feature 46). */}
        {Object.entries(SLUGS_ZONA).map(([slug, zona], n) => (
          <span key={slug}>
            {n > 0 && ' · '}
            <Link to={`/${slug}`} className="underline-offset-2 hover:underline">
              {zona}
            </Link>
          </span>
        ))}{' '}
        — y cualquier lugar de Colombia. Sin costo, sin fricción: solo tu nombre y un teléfono de
        contacto.
      </p>
    </div>
  );
}
