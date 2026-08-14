import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ApiError,
  crearAvistamiento,
  eliminarReporte,
  listarAvistamientos,
  listarCoincidencias,
  suscribirseANovedades,
  marcarReunido,
  mediaUrl,
  obtenerReporte,
} from '../api/client';
import type { Avistamiento, Coincidencia, Reporte } from '../api/types';
import { AvisoSeguridad } from '../components/AvisoSeguridad';
import { ContactoBotones } from '../components/ContactoBotones';
import { MapaLienzo } from '../components/MapaLienzo';
import { urlPerfilPlataforma } from '../lib/contacto';
import { getActiveUserId } from '../lib/session';
import { tiempoRelativo } from '../lib/tiempo';
import { tituloReporte } from '../lib/titulo';

const ETIQUETA_TIPO = {
  perdido: { texto: 'Se perdió', color: 'bg-danger' },
  encontrado: { texto: 'Encontrada', color: 'bg-forest' },
} as const;

const ETIQUETA_ESPECIE = { perro: 'Perro', gato: 'Gato', otro: 'Otro animal' } as const;

const ETIQUETA_SITUACION = {
  conmigo: 'La tiene resguardada quien la reportó',
  vista: 'Fue vista, pero no la pudieron atrapar',
} as const;

const ETIQUETA_PLATAFORMA = {
  instagram: 'Instagram',
  facebook: 'Facebook',
  whatsapp: 'WhatsApp',
  x: 'X',
  tiktok: 'TikTok',
  desconocida: 'redes sociales',
} as const;

function formatearFecha(iso: string): string {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

function hoyISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export function ReporteDetalle() {
  const { id } = useParams<{ id: string }>();
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const [coincidencias, setCoincidencias] = useState<Coincidencia[]>([]);
  const [avistamientos, setAvistamientos] = useState<Avistamiento[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [confirmandoEliminar, setConfirmandoEliminar] = useState(false);
  const [eliminando, setEliminando] = useState(false);
  const [errorEliminar, setErrorEliminar] = useState<string | null>(null);
  const [avisoCompartir, setAvisoCompartir] = useState<string | null>(null);
  const [mostrandoFormAvistamiento, setMostrandoFormAvistamiento] = useState(false);
  const [pinAvistamiento, setPinAvistamiento] = useState<{ lat: number; lng: number } | null>(null);
  const [fechaAvistamiento, setFechaAvistamiento] = useState(hoyISO());
  const [comentarioAvistamiento, setComentarioAvistamiento] = useState('');
  const [nombreAvistamiento, setNombreAvistamiento] = useState('');
  const [enviandoAvistamiento, setEnviandoAvistamiento] = useState(false);
  const [emailNovedades, setEmailNovedades] = useState('');
  const [fotoActiva, setFotoActiva] = useState(0);
  const [estadoNovedades, setEstadoNovedades] = useState<'idle' | 'enviando' | 'ok' | 'error'>(
    'idle',
  );
  const [errorAvistamiento, setErrorAvistamiento] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    obtenerReporte(Number(id)).then(setReporte);
    listarCoincidencias(Number(id)).then(setCoincidencias);
    listarAvistamientos(Number(id)).then(setAvistamientos);
  }, [id]);

  if (!reporte) {
    return <div className="mx-auto mt-8 h-96 max-w-2xl animate-pulse rounded-2xl bg-surface-alt" />;
  }

  const fotos = reporte.fotos?.length ? reporte.fotos : reporte.foto_url ? [reporte.foto_url] : [];
  const tipo = ETIQUETA_TIPO[reporte.tipo];
  const titulo = tituloReporte(reporte);
  const lugar = reporte.zona === 'Otro' ? reporte.ciudad_texto ?? 'Colombia' : reporte.zona;
  const enlaceOriginal =
    reporte.crawl_metadata?.url_post ??
    (reporte.crawl_metadata?.autor_handle
      ? urlPerfilPlataforma(reporte.crawl_metadata.plataforma, reporte.crawl_metadata.autor_handle)
      : null);

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <button type="button" onClick={() => navigate(-1)} className="text-sm text-muted">
        ← Volver
      </button>

      {/* La foto completa, sin recorte (object-contain con tope de alto): las
          señas de la mascota pueden estar justo en lo que un crop 4:3 corta.
          Con varias fotos (feature 41), miniaturas para cambiar la grande. */}
      {fotos.length > 0 && (
        <div className="flex flex-col gap-2">
          <img
            src={mediaUrl(fotos[Math.min(fotoActiva, fotos.length - 1)])}
            alt={`Foto del reporte de ${titulo}`}
            className="max-h-[75vh] w-full rounded-[22px] border border-line bg-surface-alt object-contain"
          />
          {fotos.length > 1 && (
            <div className="flex gap-2">
              {fotos.map((f, n) => (
                <button
                  key={f}
                  type="button"
                  aria-label={`Ver foto ${n + 1}`}
                  onClick={() => setFotoActiva(n)}
                  className={`h-16 w-16 overflow-hidden rounded-lg border-2 ${
                    n === fotoActiva ? 'border-forest' : 'border-line'
                  }`}
                >
                  <img src={mediaUrl(f)} alt="" className="h-full w-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink">{titulo}</h1>
          <p className="mt-1 text-sm text-muted">
            {ETIQUETA_ESPECIE[reporte.especie]} · {lugar}
            {reporte.barrio ? ` · ${reporte.barrio}` : ''} · {formatearFecha(reporte.fecha_evento)}
            {' · '}
            Publicado {tiempoRelativo(reporte.creado_en)}
          </p>
        </div>
        <span
          className={`rounded-md px-3 py-1 font-mono text-xs tracking-wide text-bg ${tipo.color}`}
        >
          {tipo.texto}
        </span>
      </header>

      {/* Difusión (feature 21): Web Share API nativa, con fallback a copiar el
          link — la vista previa bonita la ponen los og tags (ADR 0010). */}
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={async () => {
            const url = window.location.href;
            const texto = `${titulo} — ${tipo.texto} en ${lugar}. Ayuda a difundir:`;
            if (navigator.share) {
              try {
                await navigator.share({ title: 'Pet Finder Col', text: texto, url });
              } catch {
                // Compartir cancelado por el usuario: no es un error.
              }
            } else {
              await navigator.clipboard.writeText(url);
              setAvisoCompartir('Link copiado — pégalo donde quieras.');
              setTimeout(() => setAvisoCompartir(null), 3000);
            }
          }}
          className="rounded-full border border-line px-5 py-2 font-medium text-ink-soft"
        >
          Compartir este reporte
        </button>
        {avisoCompartir && <span className="text-sm text-forest">{avisoCompartir}</span>}
      </div>

      {reporte.estado === 'reunido' && (
        <p className="rounded-2xl border border-forest-tint-line bg-forest-tint p-4 text-sm text-forest">
          Esta mascota ya se reencontró con su familia. 💚
        </p>
      )}

      {/* El final feliz lo declara solo el autor (validado también en el backend). */}
      {reporte.estado === 'activo' && reporte.user_id === getActiveUserId() && (
        <div className="rounded-2xl border border-forest-tint-line bg-forest-tint p-4">
          <p className="mb-3 text-sm text-ink-soft">
            ¿Ya se reencontraron? Márcalo para celebrarlo y dejar de recibir contactos.
          </p>
          <button
            type="button"
            onClick={async () => {
              setError(null);
              try {
                const actualizado = await marcarReunido(reporte.id, getActiveUserId());
                setReporte(actualizado);
              } catch (err) {
                setError(
                  err instanceof ApiError
                    ? err.message
                    : 'No pudimos actualizar el reporte. Intenta de nuevo.',
                );
              }
            }}
            className="rounded-full bg-forest px-5 py-2 font-medium text-bg"
          >
            Marcar como reunida
          </button>
          {error && <p className="mt-2 text-sm text-danger">{error}</p>}
        </div>
      )}

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-2 font-display text-lg text-ink">Descripción y señas</h2>
        {(reporte.raza || reporte.color || reporte.tamano) && (
          <div className="mb-3 flex flex-wrap gap-1.5">
            {reporte.raza && (
              <span className="rounded-full bg-surface-alt px-2.5 py-1 text-xs text-ink-soft">
                {reporte.raza}
              </span>
            )}
            {reporte.color && (
              <span className="rounded-full bg-surface-alt px-2.5 py-1 text-xs text-ink-soft">
                {reporte.color}
              </span>
            )}
            {reporte.tamano && (
              <span className="rounded-full bg-surface-alt px-2.5 py-1 text-xs text-ink-soft">
                {reporte.tamano.charAt(0).toUpperCase() + reporte.tamano.slice(1)}
              </span>
            )}
          </div>
        )}
        <p className="text-ink-soft">{reporte.descripcion}</p>
        {reporte.situacion && (
          <p className="mt-3 text-sm text-muted">{ETIQUETA_SITUACION[reporte.situacion]}</p>
        )}
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-2 font-display text-lg text-ink">
          {reporte.tipo === 'perdido' ? 'Dónde se perdió' : 'Dónde la vieron o encontraron'}
        </h2>
        <MapaLienzo
          zona={reporte.zona}
          pines={[
            {
              id: reporte.id,
              lat: reporte.lat,
              lng: reporte.lng,
              colorClass: tipo.color,
              etiqueta: `Ubicación del reporte de ${titulo}`,
            },
            // Pistas de terceros como pins secundarios (ochre, ids desplazados
            // para no chocar con el id del reporte).
            ...avistamientos.map((a) => ({
              id: 1_000_000 + a.id,
              lat: a.lat,
              lng: a.lng,
              colorClass: 'bg-ochre',
              etiqueta: `Avistamiento del ${formatearFecha(a.fecha)}`,
            })),
          ]}
        />
      </section>

      {reporte.tipo === 'perdido' && reporte.estado === 'activo' && (
        <section className="rounded-2xl border border-line bg-surface p-6">
          <h2 className="mb-1 font-display text-lg text-ink">Avistamientos</h2>
          <p className="mb-4 text-sm text-ink-soft">
            ¿La viste por ahí? Deja la pista aquí — le sirve a su familia y a todos los que están
            buscando. No necesitas cuenta.
          </p>

          {avistamientos.length > 0 && (
            <ul className="mb-4 space-y-2">
              {avistamientos.map((a) => (
                <li key={a.id} className="rounded-xl bg-surface-alt p-3 text-sm text-ink-soft">
                  <span className="font-medium text-ink">Vista el {formatearFecha(a.fecha)}</span>
                  {' — '}
                  {a.comentario}
                  {a.nombre && <span className="text-muted"> ({a.nombre})</span>}
                </li>
              ))}
            </ul>
          )}

          {!mostrandoFormAvistamiento ? (
            <button
              type="button"
              onClick={() => {
                setPinAvistamiento({ lat: reporte.lat, lng: reporte.lng });
                setFechaAvistamiento(hoyISO());
                setMostrandoFormAvistamiento(true);
              }}
              className="rounded-full bg-ochre px-5 py-2 font-medium text-bg"
            >
              La vi — marcar avistamiento
            </button>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-muted">Toca el mapa en el punto exacto donde la viste.</p>
              <MapaLienzo
                zona={reporte.zona}
                pines={[
                  {
                    id: 1,
                    lat: pinAvistamiento?.lat ?? reporte.lat,
                    lng: pinAvistamiento?.lng ?? reporte.lng,
                    colorClass: 'bg-ochre',
                    etiqueta: 'Pin del avistamiento',
                  },
                ]}
                onClickCoords={setPinAvistamiento}
              />
              <div>
                <label htmlFor="avistamiento-fecha" className="text-sm font-medium text-ink-soft">
                  ¿Cuándo la viste?
                </label>
                <input
                  id="avistamiento-fecha"
                  type="date"
                  value={fechaAvistamiento}
                  onChange={(e) => setFechaAvistamiento(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
                />
              </div>
              <div>
                <label
                  htmlFor="avistamiento-comentario"
                  className="text-sm font-medium text-ink-soft"
                >
                  ¿Qué viste?
                </label>
                <input
                  id="avistamiento-comentario"
                  type="text"
                  maxLength={200}
                  placeholder="Ej: corría hacia el parque, se veía asustada"
                  value={comentarioAvistamiento}
                  onChange={(e) => setComentarioAvistamiento(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
                />
              </div>
              <div>
                <label htmlFor="avistamiento-nombre" className="text-sm font-medium text-ink-soft">
                  Tu nombre (opcional)
                </label>
                <input
                  id="avistamiento-nombre"
                  type="text"
                  value={nombreAvistamiento}
                  onChange={(e) => setNombreAvistamiento(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
                />
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={enviandoAvistamiento}
                  onClick={async () => {
                    if (!comentarioAvistamiento.trim()) {
                      setErrorAvistamiento('Cuéntanos qué viste (el comentario es obligatorio).');
                      return;
                    }
                    setErrorAvistamiento(null);
                    setEnviandoAvistamiento(true);
                    try {
                      const nuevo = await crearAvistamiento(reporte.id, {
                        lat: pinAvistamiento?.lat ?? reporte.lat,
                        lng: pinAvistamiento?.lng ?? reporte.lng,
                        fecha: fechaAvistamiento,
                        comentario: comentarioAvistamiento.trim(),
                        nombre: nombreAvistamiento.trim() || undefined,
                      });
                      setAvistamientos((previos) => [nuevo, ...previos]);
                      setComentarioAvistamiento('');
                      setNombreAvistamiento('');
                      setMostrandoFormAvistamiento(false);
                    } catch (err) {
                      setErrorAvistamiento(
                        err instanceof ApiError
                          ? err.message
                          : 'No pudimos guardar el avistamiento. Intenta de nuevo.',
                      );
                    } finally {
                      setEnviandoAvistamiento(false);
                    }
                  }}
                  className="rounded-full bg-ochre px-5 py-2 font-medium text-bg disabled:opacity-60"
                >
                  {enviandoAvistamiento ? 'Guardando…' : 'Guardar avistamiento'}
                </button>
                <button
                  type="button"
                  onClick={() => setMostrandoFormAvistamiento(false)}
                  className="rounded-full border border-line px-5 py-2 font-medium text-ink-soft"
                >
                  Cancelar
                </button>
              </div>
              {errorAvistamiento && <p className="text-sm text-danger">{errorAvistamiento}</p>}
            </div>
          )}
        </section>
      )}

      {reporte.estado === 'activo' && (
        <section className="rounded-2xl border border-line bg-surface p-6">
          {/* Reporte crawleado sin teléfono (ADR 0010): el contacto es el post
              original — y a falta de su URL, el perfil de quien publicó. Sin
              nada accionable no se promete contacto (solo la procedencia). */}
          {(reporte.telefono_contacto || enlaceOriginal) && (
            <h2 className="mb-2 font-display text-lg text-ink">
              {reporte.tipo === 'perdido'
                ? '¿La viste? Avísale a su familia'
                : '¿Es tuya? Escríbele'}
            </h2>
          )}
          {reporte.telefono_contacto ? (
            <div className="flex flex-col gap-3">
              <ContactoBotones
                tipo={reporte.tipo}
                etiqueta={titulo}
                telefono={reporte.telefono_contacto}
              />
              {/* Canales opcionales (feature 40). */}
              {(reporte.instagram || reporte.facebook) && (
                <div className="flex flex-wrap gap-3">
                  {reporte.instagram && (
                    <a
                      href={urlPerfilPlataforma('instagram', reporte.instagram) ?? '#'}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-full border border-line px-5 py-2 font-medium text-ink-soft"
                    >
                      Instagram
                    </a>
                  )}
                  {reporte.facebook && (
                    <a
                      href={
                        reporte.facebook.startsWith('http')
                          ? reporte.facebook
                          : urlPerfilPlataforma('facebook', reporte.facebook) ?? '#'
                      }
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-full border border-line px-5 py-2 font-medium text-ink-soft"
                    >
                      Facebook
                    </a>
                  )}
                </div>
              )}
            </div>
          ) : enlaceOriginal ? (
            <a
              href={enlaceOriginal}
              target="_blank"
              rel="noreferrer"
              className="inline-block rounded-full bg-forest px-5 py-3 font-medium text-bg"
            >
              {reporte.crawl_metadata?.url_post
                ? 'Ver publicación original'
                : 'Ver perfil de quien publicó'}
            </a>
          ) : null}
          {reporte.fuente === 'crawl' && reporte.crawl_metadata && (
            <p className="mt-3 text-sm text-muted">
              Encontrado en {ETIQUETA_PLATAFORMA[reporte.crawl_metadata.plataforma]}
              {reporte.crawl_metadata.plataforma === 'facebook' && reporte.crawl_metadata.grupo
                ? ` (grupo ${reporte.crawl_metadata.grupo})`
                : ''}
              {reporte.crawl_metadata.plataforma === 'whatsapp' &&
              reporte.crawl_metadata.nombre_grupo
                ? ` (grupo ${reporte.crawl_metadata.nombre_grupo})`
                : ''}
              {reporte.crawl_metadata.autor_handle
                ? `, publicado por @${reporte.crawl_metadata.autor_handle}`
                : ''}
              . La información fue extraída automáticamente: verifícala en la publicación.
            </p>
          )}
        </section>
      )}

      {reporte.estado === 'activo' && (reporte.telefono_contacto || enlaceOriginal) && (
        <AvisoSeguridad contexto="contactar" />
      )}

      {/* Avísame si hay novedades (feature 39, ADR 0011): correo sin cuenta,
          baja en un click desde el propio email. */}
      {reporte.estado === 'activo' && (
        <section className="rounded-2xl border border-line bg-surface p-6">
          <h2 className="mb-1 font-display text-lg text-ink">🔔 Avísame si hay novedades</h2>
          <p className="mb-3 text-sm text-muted">
            Te escribimos cuando alguien la vea o cuando vuelva a casa. Sin cuentas: solo tu correo,
            y te das de baja con un click.
          </p>
          {estadoNovedades === 'ok' ? (
            <p className="text-sm font-medium text-forest">
              Listo: te avisaremos a {emailNovedades}.
            </p>
          ) : (
            <form
              className="flex flex-wrap gap-2"
              onSubmit={async (e) => {
                e.preventDefault();
                setEstadoNovedades('enviando');
                try {
                  await suscribirseANovedades(reporte.id, emailNovedades);
                  setEstadoNovedades('ok');
                } catch {
                  setEstadoNovedades('error');
                }
              }}
            >
              <label htmlFor="email-novedades" className="sr-only">
                Tu correo
              </label>
              <input
                id="email-novedades"
                type="email"
                required
                value={emailNovedades}
                onChange={(e) => setEmailNovedades(e.target.value)}
                placeholder="tucorreo@ejemplo.com"
                className="min-w-0 flex-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
              />
              <button
                type="submit"
                disabled={estadoNovedades === 'enviando'}
                className="rounded-full bg-forest px-5 py-2 text-sm font-medium text-bg disabled:opacity-60"
              >
                {estadoNovedades === 'enviando' ? 'Guardando…' : 'Avísame'}
              </button>
              {estadoNovedades === 'error' && (
                <p className="w-full text-sm text-danger">
                  No pudimos guardar tu correo. Revísalo e intenta de nuevo.
                </p>
              )}
            </form>
          )}
        </section>
      )}

      {reporte.estado === 'activo' && coincidencias.length > 0 && (
        <section className="rounded-2xl border border-forest-tint-line bg-forest-tint p-6">
          <h2 className="mb-1 font-display text-lg text-ink">Posibles coincidencias</h2>
          <p className="mb-4 text-sm text-ink-soft">
            {reporte.tipo === 'perdido'
              ? 'Mascotas encontradas de la misma especie, cerca de donde se perdió.'
              : 'Mascotas perdidas de la misma especie, cerca de donde la encontraste.'}
          </p>
          <ul className="space-y-3">
            {coincidencias.map((c) => (
              <li key={c.id}>
                <Link
                  to={`/reporte/${c.id}`}
                  className="flex items-center gap-4 rounded-xl border border-line bg-surface p-3"
                >
                  <span
                    className="h-14 w-14 shrink-0 rounded-lg bg-surface-alt bg-cover bg-center"
                    style={{
                      backgroundImage: c.foto_url ? `url(${mediaUrl(c.foto_url)})` : undefined,
                    }}
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium text-ink">{tituloReporte(c)}</span>
                    <span className="block truncate text-sm text-muted">{c.descripcion}</span>
                    {/* Por qué coincide (feature 37): confianza sin caja negra. */}
                    <span className="mt-1.5 flex flex-wrap gap-1">
                      {c.razones.map((razon) => (
                        <span
                          key={razon}
                          className="rounded-full bg-forest-tint px-2 py-0.5 text-xs text-forest"
                        >
                          {razon}
                        </span>
                      ))}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Borrado definitivo, solo autor, con confirmación en dos pasos dentro de
          la página (window.confirm bloquearía y desentona con el resto de la UI). */}
      {reporte.user_id === getActiveUserId() && (
        <section className="flex flex-wrap items-center gap-4 rounded-2xl border border-line bg-surface p-6">
          <Link
            to={`/reporte/${reporte.id}/editar`}
            className="rounded-full border border-line px-5 py-2 font-medium text-ink-soft"
          >
            Editar reporte
          </Link>
          {!confirmandoEliminar ? (
            <button
              type="button"
              onClick={() => setConfirmandoEliminar(true)}
              className="text-sm font-medium text-danger"
            >
              Eliminar este reporte
            </button>
          ) : (
            <div>
              <p className="mb-3 text-sm text-ink-soft">
                ¿Seguro que quieres eliminar este reporte? Esta acción no se puede deshacer.
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={eliminando}
                  onClick={async () => {
                    setErrorEliminar(null);
                    setEliminando(true);
                    try {
                      await eliminarReporte(reporte.id, getActiveUserId());
                      navigate('/reportes');
                    } catch (err) {
                      setErrorEliminar(
                        err instanceof ApiError
                          ? err.message
                          : 'No pudimos eliminar el reporte. Intenta de nuevo.',
                      );
                      setEliminando(false);
                    }
                  }}
                  className="rounded-full bg-danger px-5 py-2 font-medium text-bg disabled:opacity-60"
                >
                  {eliminando ? 'Eliminando…' : 'Sí, eliminar'}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmandoEliminar(false)}
                  className="rounded-full border border-line px-5 py-2 font-medium text-ink-soft"
                >
                  Cancelar
                </button>
              </div>
              {errorEliminar && <p className="mt-2 text-sm text-danger">{errorEliminar}</p>}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
