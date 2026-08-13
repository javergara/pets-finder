import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listarOrganizaciones, mediaUrl } from '../api/client';
import type { Organizacion, TipoOrganizacion } from '../api/types';
import { MapaLienzo } from '../components/MapaLienzo';
import { NOMBRES_ZONAS } from '../lib/ciudades';
import { ETIQUETA_TIPO_ORGANIZACION, TIPOS_ORGANIZACION } from '../lib/organizaciones';

export function RedDeApoyo() {
  const [organizaciones, setOrganizaciones] = useState<Organizacion[]>([]);
  const [tipo, setTipo] = useState<TipoOrganizacion | ''>('');
  const [zona, setZona] = useState('');

  useEffect(() => {
    listarOrganizaciones({ tipo: tipo || undefined, zona: zona || undefined }).then(
      setOrganizaciones,
    );
  }, [tipo, zona]);

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6 pb-24">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink">Centros de ayuda</h1>
          <p className="mt-1 max-w-xl text-sm text-muted">
            Centros de acopio, fundaciones, tiendas y veterinarias que están ayudando. Encuentra
            dónde llevar donaciones o a quién acudir.
          </p>
        </div>
        <Link
          to="/ayudar/registrar"
          className="shrink-0 rounded-full bg-forest px-5 py-3 font-medium text-bg"
        >
          Registrar un lugar
        </Link>
      </header>

      {/* Chips de tipo: filtro y leyenda de colores a la vez. */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setTipo('')}
          className={`rounded-full border px-3 py-1.5 text-sm ${
            tipo === '' ? 'border-forest bg-forest-tint text-forest' : 'border-line text-muted'
          }`}
        >
          Todos
        </button>
        {TIPOS_ORGANIZACION.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTipo(tipo === t ? '' : t)}
            className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm ${
              tipo === t ? 'border-forest bg-forest-tint text-forest' : 'border-line text-muted'
            }`}
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${ETIQUETA_TIPO_ORGANIZACION[t].color}`}
              aria-hidden
            />
            {ETIQUETA_TIPO_ORGANIZACION[t].texto}
          </button>
        ))}
        <select
          aria-label="Zona"
          value={zona}
          onChange={(e) => setZona(e.target.value)}
          className="ml-auto rounded-xl border border-line bg-surface px-3 py-1.5 text-sm text-ink"
        >
          <option value="">Todo Colombia</option>
          {NOMBRES_ZONAS.map((nombre) => (
            <option key={nombre} value={nombre}>
              {nombre}
            </option>
          ))}
        </select>
      </div>

      <MapaLienzo
        zona={zona || 'Colombia'}
        pines={organizaciones.map((o) => ({
          id: o.id,
          lat: o.lat,
          lng: o.lng,
          colorClass: ETIQUETA_TIPO_ORGANIZACION[o.tipo].color,
          etiqueta: `${o.nombre} (${ETIQUETA_TIPO_ORGANIZACION[o.tipo].texto})`,
        }))}
      />

      {organizaciones.length === 0 ? (
        <p className="rounded-2xl border border-line bg-surface p-6 text-sm text-muted">
          Aún no hay lugares registrados con estos filtros. ¿Conoces uno? Regístralo y ayuda a que
          más gente lo encuentre.
        </p>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2">
          {organizaciones.map((o) => (
            <li key={o.id}>
              <Link
                to={`/organizacion/${o.id}`}
                className="flex h-full flex-col overflow-hidden rounded-[22px] border border-line bg-surface transition-shadow hover:shadow-[0_18px_40px_-28px_rgba(27,26,23,.5)]"
              >
                {o.foto_url && (
                  <div className="relative aspect-[3/1] bg-surface-alt">
                    <img
                      src={mediaUrl(o.foto_url)}
                      alt={`Foto de ${o.nombre}`}
                      loading="lazy"
                      className="absolute inset-0 h-full w-full object-cover"
                    />
                  </div>
                )}
                <div className="flex flex-1 flex-col p-4">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-display text-lg text-ink">{o.nombre}</h3>
                    <span
                      className={`shrink-0 rounded-md px-2 py-1 font-mono text-[11px] tracking-wide text-bg ${
                        ETIQUETA_TIPO_ORGANIZACION[o.tipo].color
                      }`}
                    >
                      {ETIQUETA_TIPO_ORGANIZACION[o.tipo].texto}
                    </span>
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-muted">{o.descripcion}</p>
                  {o.necesidades_pendientes > 0 && (
                    <p className="mt-2 text-xs font-medium text-ochre">
                      {o.necesidades_pendientes}{' '}
                      {o.necesidades_pendientes === 1 ? 'necesidad activa' : 'necesidades activas'}
                    </p>
                  )}
                  <div className="mt-3 flex items-center justify-between border-t border-line-soft pt-3 text-xs text-muted">
                    <span>
                      {o.direccion} · {o.zona === 'Otro' ? o.ciudad_texto ?? 'Colombia' : o.zona}
                    </span>
                    {o.horario && <span className="shrink-0">{o.horario}</span>}
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
