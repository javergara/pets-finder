import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ApiError,
  crearNecesidad,
  cubrirNecesidad,
  editarOrganizacion,
  eliminarOrganizacion,
  listarNecesidades,
  mediaUrl,
  obtenerOrganizacion,
} from '../api/client';
import type { CategoriaNecesidad, Necesidad, Organizacion } from '../api/types';
import { MapaLienzo } from '../components/MapaLienzo';
import {
  mensajeAyudaOrganizacion,
  mensajeQuieroAyudar,
  urlTelefono,
  urlWhatsApp,
} from '../lib/contacto';
import {
  CATEGORIAS_NECESIDAD,
  ETIQUETA_CATEGORIA_NECESIDAD,
  ETIQUETA_TIPO_ORGANIZACION,
} from '../lib/organizaciones';
import { getActiveUserId } from '../lib/session';

export function OrganizacionDetalle() {
  const { id } = useParams<{ id: string }>();
  const [organizacion, setOrganizacion] = useState<Organizacion | null>(null);
  const [necesidades, setNecesidades] = useState<Necesidad[]>([]);
  const [categoriaNueva, setCategoriaNueva] = useState<CategoriaNecesidad>('alimento');
  const [descripcionNueva, setDescripcionNueva] = useState('');
  const [publicando, setPublicando] = useState(false);
  const [errorNecesidad, setErrorNecesidad] = useState<string | null>(null);
  const [editando, setEditando] = useState(false);
  const [descripcion, setDescripcion] = useState('');
  const [telefono, setTelefono] = useState('');
  const [horario, setHorario] = useState('');
  const [comoDonar, setComoDonar] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [confirmandoEliminar, setConfirmandoEliminar] = useState(false);
  const [eliminando, setEliminando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    obtenerOrganizacion(Number(id)).then(setOrganizacion);
    listarNecesidades(Number(id)).then(setNecesidades);
  }, [id]);

  if (!organizacion) {
    return <div className="mx-auto mt-8 h-96 max-w-2xl animate-pulse rounded-2xl bg-surface-alt" />;
  }

  const etiqueta = ETIQUETA_TIPO_ORGANIZACION[organizacion.tipo];
  const lugar =
    organizacion.zona === 'Otro' ? organizacion.ciudad_texto ?? 'Colombia' : organizacion.zona;
  const esAutor = organizacion.user_id === getActiveUserId();

  async function guardarCambios() {
    if (!organizacion) return;
    setError(null);
    setGuardando(true);
    try {
      const actualizada = await editarOrganizacion(organizacion.id, {
        user_id: getActiveUserId(),
        descripcion: descripcion.trim() || undefined,
        telefono_contacto: telefono.trim() || undefined,
        horario: horario.trim() || undefined,
        como_donar: comoDonar.trim() || undefined,
      });
      setOrganizacion(actualizada);
      setEditando(false);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'No pudimos guardar los cambios. Intenta de nuevo.',
      );
    } finally {
      setGuardando(false);
    }
  }

  async function cambiarEstado(estado: 'activo' | 'cerrado') {
    if (!organizacion) return;
    setError(null);
    try {
      setOrganizacion(
        await editarOrganizacion(organizacion.id, { user_id: getActiveUserId(), estado }),
      );
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'No pudimos actualizar el estado. Intenta de nuevo.',
      );
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <button type="button" onClick={() => navigate(-1)} className="text-sm text-muted">
        ← Volver
      </button>

      {organizacion.foto_url && (
        <img
          src={mediaUrl(organizacion.foto_url)}
          alt={`Foto de ${organizacion.nombre}`}
          className="max-h-[50vh] w-full rounded-[22px] border border-line bg-surface-alt object-contain"
        />
      )}

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink">{organizacion.nombre}</h1>
          <p className="mt-1 text-sm text-muted">
            {lugar}
            {organizacion.barrio ? ` · ${organizacion.barrio}` : ''} · {organizacion.direccion}
          </p>
        </div>
        <span
          className={`rounded-md px-3 py-1 font-mono text-xs tracking-wide text-bg ${etiqueta.color}`}
        >
          {etiqueta.texto}
        </span>
      </header>

      {organizacion.estado === 'cerrado' && (
        <p className="rounded-2xl border border-line bg-surface-alt p-4 text-sm text-muted">
          Este lugar está marcado como cerrado.
        </p>
      )}

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-2 font-display text-lg text-ink">Qué hacen</h2>
        <p className="text-ink-soft">{organizacion.descripcion}</p>
        {organizacion.horario && (
          <p className="mt-3 text-sm text-muted">Horario: {organizacion.horario}</p>
        )}
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="mb-2 font-display text-lg text-ink">Dónde están</h2>
        <MapaLienzo
          zona={organizacion.zona}
          pines={[
            {
              id: organizacion.id,
              lat: organizacion.lat,
              lng: organizacion.lng,
              colorClass: etiqueta.color,
              etiqueta: `Ubicación de ${organizacion.nombre}`,
            },
          ]}
        />
      </section>

      {organizacion.como_donar && (
        <section className="rounded-2xl border border-forest-tint-line bg-forest-tint p-6">
          <h2 className="mb-2 font-display text-lg text-ink">Cómo donar</h2>
          <p className="text-ink-soft">{organizacion.como_donar}</p>
        </section>
      )}

      {(necesidades.length > 0 || esAutor) && (
        <section className="rounded-2xl border border-line bg-surface p-6">
          <h2 className="mb-1 font-display text-lg text-ink">Necesidades</h2>
          <p className="mb-4 text-sm text-ink-soft">
            Ayuda concreta que están pidiendo. Toma una y escríbeles directo.
          </p>

          {necesidades.length > 0 && (
            <ul className="space-y-2">
              {necesidades.map((n) => (
                <li
                  key={n.id}
                  className={`flex flex-wrap items-center justify-between gap-3 rounded-xl p-3 ${
                    n.estado === 'cubierta'
                      ? 'border border-forest-tint-line bg-forest-tint'
                      : 'bg-surface-alt'
                  }`}
                >
                  <span className="min-w-0 flex-1 text-sm text-ink-soft">
                    <span className="mr-2 rounded-full bg-surface px-2 py-0.5 text-xs text-muted">
                      {ETIQUETA_CATEGORIA_NECESIDAD[n.categoria]}
                    </span>
                    {n.descripcion}
                  </span>
                  {n.estado === 'cubierta' ? (
                    <span className="shrink-0 text-sm font-medium text-forest">Cubierta 💚</span>
                  ) : (
                    <span className="flex shrink-0 items-center gap-3">
                      <a
                        href={urlWhatsApp(
                          organizacion.telefono_contacto,
                          mensajeQuieroAyudar(n.descripcion),
                        )}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded-full bg-forest px-4 py-1.5 text-sm font-medium text-bg"
                      >
                        Quiero ayudar
                      </a>
                      {esAutor && (
                        <button
                          type="button"
                          onClick={async () => {
                            setErrorNecesidad(null);
                            try {
                              const cubierta = await cubrirNecesidad(
                                organizacion.id,
                                n.id,
                                getActiveUserId(),
                              );
                              setNecesidades((previas) =>
                                previas.map((p) => (p.id === cubierta.id ? cubierta : p)),
                              );
                            } catch (err) {
                              setErrorNecesidad(
                                err instanceof ApiError
                                  ? err.message
                                  : 'No pudimos actualizar la necesidad. Intenta de nuevo.',
                              );
                            }
                          }}
                          className="text-sm font-medium text-muted underline-offset-4 hover:underline"
                        >
                          Marcar cubierta
                        </button>
                      )}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}

          {esAutor && organizacion.estado === 'activo' && (
            <div className="mt-4 flex flex-wrap items-end gap-3 border-t border-line-soft pt-4">
              <div>
                <label htmlFor="necesidad-categoria" className="text-sm font-medium text-ink-soft">
                  Categoría
                </label>
                <select
                  id="necesidad-categoria"
                  value={categoriaNueva}
                  onChange={(e) => setCategoriaNueva(e.target.value as CategoriaNecesidad)}
                  className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-ink"
                >
                  {CATEGORIAS_NECESIDAD.map((c) => (
                    <option key={c} value={c}>
                      {ETIQUETA_CATEGORIA_NECESIDAD[c]}
                    </option>
                  ))}
                </select>
              </div>
              <div className="min-w-0 flex-1">
                <label
                  htmlFor="necesidad-descripcion"
                  className="text-sm font-medium text-ink-soft"
                >
                  ¿Qué necesitan?
                </label>
                <input
                  id="necesidad-descripcion"
                  type="text"
                  maxLength={300}
                  placeholder="Ej: 50 kg de comida para perro adulto"
                  value={descripcionNueva}
                  onChange={(e) => setDescripcionNueva(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
                />
              </div>
              <button
                type="button"
                disabled={publicando}
                onClick={async () => {
                  if (!descripcionNueva.trim()) {
                    setErrorNecesidad('Describe qué necesitan.');
                    return;
                  }
                  setErrorNecesidad(null);
                  setPublicando(true);
                  try {
                    const nueva = await crearNecesidad(organizacion.id, {
                      user_id: getActiveUserId(),
                      categoria: categoriaNueva,
                      descripcion: descripcionNueva.trim(),
                    });
                    setNecesidades((previas) => [nueva, ...previas]);
                    setDescripcionNueva('');
                  } catch (err) {
                    setErrorNecesidad(
                      err instanceof ApiError
                        ? err.message
                        : 'No pudimos publicar la necesidad. Intenta de nuevo.',
                    );
                  } finally {
                    setPublicando(false);
                  }
                }}
                className="rounded-full bg-forest px-5 py-2 font-medium text-bg disabled:opacity-60"
              >
                {publicando ? 'Publicando…' : 'Publicar'}
              </button>
            </div>
          )}
          {errorNecesidad && <p className="mt-2 text-sm text-danger">{errorNecesidad}</p>}
        </section>
      )}

      {organizacion.estado === 'activo' && (
        <section className="rounded-2xl border border-line bg-surface p-6">
          <h2 className="mb-2 font-display text-lg text-ink">Contacto</h2>
          <div className="flex flex-wrap gap-3">
            <a
              href={urlWhatsApp(
                organizacion.telefono_contacto,
                mensajeAyudaOrganizacion(organizacion.nombre),
              )}
              target="_blank"
              rel="noreferrer"
              className="rounded-full bg-forest px-5 py-3 font-medium text-bg"
            >
              Escribir por WhatsApp
            </a>
            <a
              href={urlTelefono(organizacion.telefono_contacto)}
              className="rounded-full border border-line px-5 py-3 font-medium text-ink"
            >
              Llamar
            </a>
          </div>
        </section>
      )}

      {esAutor && (
        <section className="space-y-4 rounded-2xl border border-line bg-surface p-6">
          <h2 className="font-display text-lg text-ink">Administrar</h2>
          {!editando ? (
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => {
                  setDescripcion(organizacion.descripcion);
                  setTelefono(organizacion.telefono_contacto);
                  setHorario(organizacion.horario ?? '');
                  setComoDonar(organizacion.como_donar ?? '');
                  setEditando(true);
                }}
                className="rounded-full border border-line px-5 py-2 font-medium text-ink-soft"
              >
                Editar información
              </button>
              {organizacion.estado === 'activo' ? (
                <button
                  type="button"
                  onClick={() => cambiarEstado('cerrado')}
                  className="rounded-full border border-line px-5 py-2 font-medium text-ink-soft"
                >
                  Marcar como cerrado
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => cambiarEstado('activo')}
                  className="rounded-full bg-forest px-5 py-2 font-medium text-bg"
                >
                  Reabrir
                </button>
              )}
              {!confirmandoEliminar ? (
                <button
                  type="button"
                  onClick={() => setConfirmandoEliminar(true)}
                  className="text-sm font-medium text-danger"
                >
                  Eliminar este lugar
                </button>
              ) : (
                <span className="flex flex-wrap items-center gap-3">
                  <span className="text-sm text-ink-soft">¿Seguro? No se puede deshacer.</span>
                  <button
                    type="button"
                    disabled={eliminando}
                    onClick={async () => {
                      setEliminando(true);
                      try {
                        await eliminarOrganizacion(organizacion.id, getActiveUserId());
                        navigate('/ayudar');
                      } catch (err) {
                        setError(
                          err instanceof ApiError
                            ? err.message
                            : 'No pudimos eliminar el lugar. Intenta de nuevo.',
                        );
                        setEliminando(false);
                      }
                    }}
                    className="rounded-full bg-danger px-4 py-1.5 text-sm font-medium text-bg disabled:opacity-60"
                  >
                    Sí, eliminar
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmandoEliminar(false)}
                    className="text-sm font-medium text-muted"
                  >
                    Cancelar
                  </button>
                </span>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label htmlFor="org-descripcion" className="text-sm font-medium text-ink-soft">
                  Qué hacen
                </label>
                <textarea
                  id="org-descripcion"
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  rows={3}
                  className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
                />
              </div>
              <div>
                <label htmlFor="org-telefono" className="text-sm font-medium text-ink-soft">
                  Teléfono / WhatsApp
                </label>
                <input
                  id="org-telefono"
                  type="tel"
                  value={telefono}
                  onChange={(e) => setTelefono(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
                />
              </div>
              <div>
                <label htmlFor="org-horario" className="text-sm font-medium text-ink-soft">
                  Horario
                </label>
                <input
                  id="org-horario"
                  type="text"
                  value={horario}
                  onChange={(e) => setHorario(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
                />
              </div>
              <div>
                <label htmlFor="org-donar" className="text-sm font-medium text-ink-soft">
                  Cómo donar (Nequi, cuenta, link — opcional)
                </label>
                <input
                  id="org-donar"
                  type="text"
                  value={comoDonar}
                  onChange={(e) => setComoDonar(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
                />
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={guardando}
                  onClick={guardarCambios}
                  className="rounded-full bg-forest px-5 py-2 font-medium text-bg disabled:opacity-60"
                >
                  {guardando ? 'Guardando…' : 'Guardar cambios'}
                </button>
                <button
                  type="button"
                  onClick={() => setEditando(false)}
                  className="rounded-full border border-line px-5 py-2 font-medium text-ink-soft"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
          {error && <p className="text-sm text-danger">{error}</p>}
        </section>
      )}
    </div>
  );
}
