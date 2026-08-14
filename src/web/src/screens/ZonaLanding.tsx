import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listarOrganizaciones, listarReportesPaginado, obtenerConteos } from '../api/client';
import type { Conteos, Organizacion, Reporte } from '../api/types';
import { ReporteCard } from '../components/ReporteCard';
import { ETIQUETA_TIPO_ORGANIZACION } from '../lib/organizaciones';

// Landing por zona (feature 46, plan de impacto Cali C3): la página que
// captura "perro perdido Cali" y recibe a quien llega del cartel o de un
// compartido — todo lo de la zona en una sola vista, con SEO propio.
export function ZonaLanding({ zona }: { zona: string }) {
  const [conteos, setConteos] = useState<Conteos | null>(null);
  const [recientes, setRecientes] = useState<Reporte[]>([]);
  const [organizaciones, setOrganizaciones] = useState<Organizacion[]>([]);

  useEffect(() => {
    // SEO de la SPA: Google ejecuta JS y toma este título por ruta.
    document.title = `Mascotas perdidas y encontradas en ${zona} | Pet Finder Col`;
    return () => {
      document.title = 'Pet Finder Col — Mascotas perdidas y encontradas en Colombia';
    };
  }, [zona]);

  useEffect(() => {
    obtenerConteos(zona)
      .then(setConteos)
      .catch(() => setConteos(null));
    listarReportesPaginado({ zona }, 6, 0)
      .then((r) => setRecientes(r.items))
      .catch(() => setRecientes([]));
    listarOrganizaciones({ zona })
      .then(setOrganizaciones)
      .catch(() => setOrganizaciones([]));
  }, [zona]);

  const veterinarias = organizaciones.filter((o) => o.tipo === 'veterinaria');
  const apoyo = organizaciones.filter((o) => o.tipo !== 'veterinaria');

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-6 pb-24">
      <header className="text-center">
        <h1 className="font-display text-4xl text-ink">
          Mascotas perdidas y encontradas en {zona}
        </h1>
        {conteos && conteos.perdidos + conteos.encontrados > 0 && (
          <p className="mt-2 text-ink-soft">
            Ahora mismo la comunidad busca a{' '}
            <strong className="text-danger">{conteos.perdidos} perdidas</strong> y cuida{' '}
            <strong className="text-forest">{conteos.encontrados} encontradas</strong> en {zona}.
          </p>
        )}
        <div className="mx-auto mt-5 flex max-w-2xl flex-col gap-3 sm:flex-row">
          <Link
            to="/reportar/perdido"
            className="flex-1 rounded-2xl bg-danger px-6 py-4 font-medium text-bg"
          >
            Perdí a mi mascota
          </Link>
          <Link
            to="/reportar/encontrado"
            className="flex-1 rounded-2xl bg-forest px-6 py-4 font-medium text-bg"
          >
            Encontré una mascota
          </Link>
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-center gap-4 text-sm">
          <Link to="/buscar" className="font-medium text-forest underline-offset-4 hover:underline">
            🔎 Buscar por descripción
          </Link>
          <Link to="/mapa" className="font-medium text-forest underline-offset-4 hover:underline">
            Ver el mapa
          </Link>
          <Link to="/ayudar" className="font-medium text-forest underline-offset-4 hover:underline">
            Centros de ayuda
          </Link>
        </div>
      </header>

      {recientes.length > 0 && (
        <section>
          <div className="mb-3 flex items-baseline justify-between">
            <h2 className="font-display text-2xl text-ink">Reportes recientes</h2>
            <Link
              to="/reportes"
              className="text-sm font-medium text-forest underline-offset-4 hover:underline"
            >
              Ver todos
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {recientes.map((r) => (
              <ReporteCard key={r.id} reporte={r} />
            ))}
          </div>
        </section>
      )}

      {(veterinarias.length > 0 || apoyo.length > 0) && (
        <section className="grid gap-4 sm:grid-cols-2">
          {veterinarias.length > 0 && (
            <div className="rounded-2xl border border-line bg-surface p-5">
              <h2 className="mb-2 font-display text-lg text-ink">Veterinarias en {zona}</h2>
              <ul className="space-y-2 text-sm">
                {veterinarias.slice(0, 6).map((v) => (
                  <li key={v.id} className="flex items-baseline justify-between gap-2">
                    <Link to={`/organizacion/${v.id}`} className="text-forest hover:underline">
                      {v.nombre}
                    </Link>
                    {v.horario?.toLowerCase().includes('24') && (
                      <span className="shrink-0 rounded-full bg-forest-tint px-2 py-0.5 text-xs text-forest">
                        24 horas
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {apoyo.length > 0 && (
            <div className="rounded-2xl border border-line bg-surface p-5">
              <h2 className="mb-2 font-display text-lg text-ink">Red de apoyo en {zona}</h2>
              <ul className="space-y-2 text-sm">
                {apoyo.slice(0, 6).map((o) => (
                  <li key={o.id} className="flex items-baseline justify-between gap-2">
                    <Link to={`/organizacion/${o.id}`} className="text-forest hover:underline">
                      {o.nombre}
                    </Link>
                    <span className="shrink-0 text-xs text-muted">
                      {ETIQUETA_TIPO_ORGANIZACION[o.tipo].texto}
                    </span>
                  </li>
                ))}
              </ul>
              <Link
                to="/ayudar"
                className="mt-3 inline-block text-sm font-medium text-forest underline-offset-4 hover:underline"
              >
                Ver toda la red de apoyo
              </Link>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
