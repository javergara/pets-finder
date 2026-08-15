import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  eliminarAvisoAyuda,
  listarAvisosAyuda,
  listarOrganizaciones,
  mediaUrl,
  resolverAvisoAyuda,
} from '../api/client';
import type { AvisoAyuda, Organizacion, TipoOrganizacion } from '../api/types';
import { AvisoSeguridad } from '../components/AvisoSeguridad';
import { MapaLienzo } from '../components/MapaLienzo';
import { CATEGORIAS_AVISO, ETIQUETA_CATEGORIA_AVISO, ETIQUETA_TIPO_AVISO } from '../lib/avisos';
import { NOMBRES_ZONAS } from '../lib/ciudades';
import { urlWhatsApp } from '../lib/contacto';
import { ETIQUETA_TIPO_ORGANIZACION, TIPOS_ORGANIZACION } from '../lib/organizaciones';
import { esUsuarioActivo, getActiveUserId } from '../lib/session';
import { tiempoRelativo } from '../lib/tiempo';

export function RedDeApoyo() {
  const [busqueda] = useSearchParams();
  const [pestana, setPestana] = useState<'lugares' | 'comunidad'>(
    busqueda.get('tab') === 'comunidad' ? 'comunidad' : 'lugares',
  );
  const [organizaciones, setOrganizaciones] = useState<Organizacion[]>([]);
  const [tipo, setTipo] = useState<TipoOrganizacion | ''>('');
  const [zona, setZona] = useState('');
  // Comunidad (feature 42): avisos de ayuda entre personas.
  const [avisos, setAvisos] = useState<AvisoAyuda[]>([]);
  const [tipoAviso, setTipoAviso] = useState<'pido' | 'ofrezco' | ''>('');
  const [categoriaAviso, setCategoriaAviso] = useState('');
  const [zonaAviso, setZonaAviso] = useState('');

  useEffect(() => {
    listarOrganizaciones({ tipo: tipo || undefined, zona: zona || undefined }).then(
      setOrganizaciones,
    );
  }, [tipo, zona]);

  useEffect(() => {
    if (pestana !== 'comunidad') return;
    listarAvisosAyuda({
      tipo: tipoAviso || undefined,
      categoria: categoriaAviso || undefined,
      zona: zonaAviso || undefined,
    }).then(setAvisos);
  }, [pestana, tipoAviso, categoriaAviso, zonaAviso]);

  async function resolver(aviso: AvisoAyuda) {
    const actualizado = await resolverAvisoAyuda(aviso.id, getActiveUserId());
    setAvisos((prev) => prev.map((a) => (a.id === aviso.id ? actualizado : a)));
  }

  async function eliminar(aviso: AvisoAyuda) {
    await eliminarAvisoAyuda(aviso.id, getActiveUserId());
    setAvisos((prev) => prev.filter((a) => a.id !== aviso.id));
  }

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

      {/* Pestañas (feature 42): lugares con dirección vs ayuda entre personas. */}
      <div className="flex gap-2 border-b border-line">
        {(
          [
            ['lugares', 'Lugares'],
            ['comunidad', 'Comunidad'],
          ] as const
        ).map(([clave, texto]) => (
          <button
            key={clave}
            type="button"
            onClick={() => setPestana(clave)}
            className={`-mb-px border-b-2 px-4 py-2 font-medium ${
              pestana === clave ? 'border-forest text-forest' : 'border-transparent text-muted'
            }`}
          >
            {texto}
          </button>
        ))}
      </div>

      {pestana === 'comunidad' && (
        <section className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-sm text-muted">
              Ayuda puntual entre vecinos: hogar de paso, transporte, alimento, rescate.
            </p>
            <div className="ml-auto flex gap-2">
              <Link
                to="/ayudar/publicar-aviso?tipo=pido"
                className="rounded-full bg-danger px-4 py-2 text-sm font-medium text-bg"
              >
                Necesito ayuda
              </Link>
              <Link
                to="/ayudar/publicar-aviso?tipo=ofrezco"
                className="rounded-full bg-forest px-4 py-2 text-sm font-medium text-bg"
              >
                Quiero ayudar
              </Link>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {(['', 'pido', 'ofrezco'] as const).map((t) => (
              <button
                key={t || 'todos'}
                type="button"
                onClick={() => setTipoAviso(t)}
                className={`rounded-full border px-3 py-1.5 text-sm ${
                  tipoAviso === t
                    ? 'border-forest bg-forest-tint text-forest'
                    : 'border-line text-muted'
                }`}
              >
                {t === '' ? 'Todos' : ETIQUETA_TIPO_AVISO[t].texto}
              </button>
            ))}
            <select
              aria-label="Categoría"
              value={categoriaAviso}
              onChange={(e) => setCategoriaAviso(e.target.value)}
              className="rounded-xl border border-line bg-surface px-3 py-1.5 text-sm text-ink"
            >
              <option value="">Todas las categorías</option>
              {CATEGORIAS_AVISO.map((cat) => (
                <option key={cat} value={cat}>
                  {ETIQUETA_CATEGORIA_AVISO[cat]}
                </option>
              ))}
            </select>
            <select
              aria-label="Zona de la comunidad"
              value={zonaAviso}
              onChange={(e) => setZonaAviso(e.target.value)}
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

          <AvisoSeguridad contexto="contactar" />

          {avisos.length === 0 ? (
            <p className="rounded-2xl border border-line bg-surface p-6 text-sm text-muted">
              No hay avisos activos con estos filtros. Sé la primera persona en publicar uno.
            </p>
          ) : (
            <ul className="grid gap-4 sm:grid-cols-2">
              {avisos.map((a) => (
                <li
                  key={a.id}
                  className="flex h-full flex-col rounded-[22px] border border-line bg-surface p-4"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span
                      className={`rounded-md px-2 py-1 font-mono text-[11px] tracking-wide text-bg ${
                        ETIQUETA_TIPO_AVISO[a.tipo].color
                      }`}
                    >
                      {ETIQUETA_TIPO_AVISO[a.tipo].texto}
                    </span>
                    <span className="rounded-full bg-surface-alt px-2.5 py-1 text-xs text-ink-soft">
                      {ETIQUETA_CATEGORIA_AVISO[a.categoria]}
                    </span>
                  </div>
                  <h3 className="mt-2 font-display text-lg text-ink">{a.titulo}</h3>
                  <p className="mt-1 line-clamp-3 text-sm text-muted">{a.descripcion}</p>
                  <div className="mt-2 text-xs text-muted">
                    {a.zona === 'Otro' ? a.ciudad_texto ?? 'Colombia' : a.zona}
                    {a.barrio ? ` · ${a.barrio}` : ''} · {tiempoRelativo(a.creado_en)}
                  </div>
                  {a.estado === 'resuelto' ? (
                    <p className="mt-3 text-sm font-medium text-forest">Resuelto 💚</p>
                  ) : (
                    <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-line-soft pt-3">
                      <a
                        href={urlWhatsApp(
                          a.telefono_contacto,
                          `Hola, vi tu aviso en Pet Finder Col: "${a.titulo}".`,
                        )}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded-full bg-forest px-4 py-2 text-sm font-medium text-bg"
                      >
                        WhatsApp
                      </a>
                      {esUsuarioActivo(a.user_id) && (
                        <>
                          <button
                            type="button"
                            onClick={() => resolver(a)}
                            className="rounded-full border border-forest px-4 py-2 text-sm font-medium text-forest"
                          >
                            Marcar resuelto 💚
                          </button>
                          <button
                            type="button"
                            onClick={() => eliminar(a)}
                            className="rounded-full border border-line px-4 py-2 text-sm text-muted"
                          >
                            Eliminar
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {pestana === 'lugares' && (
        <>
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
              Aún no hay lugares registrados con estos filtros. ¿Conoces uno? Regístralo y ayuda a
              que más gente lo encuentre.
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
                          {o.necesidades_pendientes === 1
                            ? 'necesidad activa'
                            : 'necesidades activas'}
                        </p>
                      )}
                      <div className="mt-3 flex items-center justify-between border-t border-line-soft pt-3 text-xs text-muted">
                        <span>
                          {o.direccion} ·{' '}
                          {o.zona === 'Otro' ? o.ciudad_texto ?? 'Colombia' : o.zona}
                        </span>
                        {o.horario && <span className="shrink-0">{o.horario}</span>}
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
