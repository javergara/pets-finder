import { type FormEvent, useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ApiError, editarReporte, listarReportes, marcarReunido, mediaUrl } from '../api/client';
import type { Reporte } from '../api/types';
import { getActiveUserId } from '../lib/session';

const ETIQUETA_ESPECIE = { perro: 'Perro', gato: 'Gato', otro: 'Otro animal' } as const;

export function MisReportes() {
  const [reportes, setReportes] = useState<Reporte[] | null>(null);
  const [editando, setEditando] = useState<Reporte | null>(null);
  const [descripcion, setDescripcion] = useState('');
  const [telefono, setTelefono] = useState('');
  const [error, setError] = useState<string | null>(null);
  const userId = getActiveUserId();

  const cargar = useCallback(() => {
    // estado=todos: aquí sí se ven los reunidos propios (son la buena noticia).
    listarReportes({ userId, estado: 'todos' }).then(setReportes);
  }, [userId]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  async function handleReunido(reporte: Reporte) {
    setError(null);
    try {
      await marcarReunido(reporte.id, userId);
      cargar();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'No pudimos actualizar el reporte. Intenta de nuevo.',
      );
    }
  }

  function abrirEdicion(reporte: Reporte) {
    setEditando(reporte);
    setDescripcion(reporte.descripcion);
    setTelefono(reporte.telefono_contacto ?? '');
  }

  async function handleGuardarEdicion(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!editando) return;
    setError(null);
    try {
      await editarReporte(editando.id, {
        user_id: userId,
        descripcion: descripcion.trim() || undefined,
        telefono_contacto: telefono.trim() || undefined,
      });
      setEditando(null);
      cargar();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'No pudimos guardar los cambios. Intenta de nuevo.',
      );
    }
  }

  if (reportes === null) {
    return <div className="mx-auto mt-8 h-80 max-w-2xl animate-pulse rounded-2xl bg-surface-alt" />;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <header>
        <h1 className="font-display text-3xl text-ink">Mis reportes</h1>
        <p className="mt-1 text-sm text-muted">
          Cuando tu mascota vuelva a casa, márcala como reunida: tu buena noticia le da esperanza a
          los demás.
        </p>
      </header>

      {error && (
        <p className="rounded-2xl border border-danger/40 bg-danger/10 p-4 text-sm text-danger">
          {error}
        </p>
      )}

      {reportes.length === 0 ? (
        <div className="rounded-2xl border border-line bg-surface p-10 text-center">
          <p className="text-ink-soft">Todavía no has creado ningún reporte.</p>
          <Link
            to="/reportar/perdido"
            className="mt-4 inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg"
          >
            Crear un reporte
          </Link>
        </div>
      ) : (
        <ul className="space-y-4">
          {reportes.map((reporte) => (
            <li
              key={reporte.id}
              className="flex flex-wrap items-center gap-4 rounded-2xl border border-line bg-surface p-4"
            >
              <span
                className="h-16 w-16 shrink-0 rounded-xl bg-surface-alt bg-cover bg-center"
                style={{
                  backgroundImage: reporte.foto_url
                    ? `url(${mediaUrl(reporte.foto_url)})`
                    : undefined,
                }}
              />
              <div className="min-w-0 flex-1">
                <Link to={`/reporte/${reporte.id}`} className="font-display text-lg text-ink">
                  {reporte.nombre_mascota ?? ETIQUETA_ESPECIE[reporte.especie]}
                </Link>
                <p className="text-sm text-muted">
                  {reporte.tipo === 'perdido' ? 'Se perdió' : 'Encontrada'} · {reporte.zona}
                </p>
              </div>
              {reporte.estado === 'reunido' ? (
                <span className="rounded-full bg-forest-tint px-3 py-1 text-sm font-medium text-forest">
                  Reunida 💚
                </span>
              ) : (
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => abrirEdicion(reporte)}
                    className="rounded-full border border-line px-4 py-2 text-sm font-medium text-ink"
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    onClick={() => handleReunido(reporte)}
                    className="rounded-full bg-forest px-4 py-2 text-sm font-medium text-bg"
                  >
                    Marcar como reunida
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {editando && (
        <form
          onSubmit={handleGuardarEdicion}
          className="space-y-3 rounded-2xl border border-line bg-surface-alt p-5"
        >
          <h2 className="font-display text-lg text-ink">
            Editar el reporte de {editando.nombre_mascota ?? ETIQUETA_ESPECIE[editando.especie]}
          </h2>
          <div>
            <label htmlFor="editar-descripcion" className="text-sm font-medium text-ink-soft">
              Descripción y señas
            </label>
            <textarea
              id="editar-descripcion"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              rows={3}
              className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
            />
          </div>
          <div>
            <label htmlFor="editar-telefono" className="text-sm font-medium text-ink-soft">
              Teléfono de contacto
            </label>
            <input
              id="editar-telefono"
              type="tel"
              value={telefono}
              onChange={(e) => setTelefono(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
            />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="rounded-full bg-forest px-4 py-2 font-medium text-bg">
              Guardar cambios
            </button>
            <button
              type="button"
              onClick={() => setEditando(null)}
              className="rounded-full border border-line px-4 py-2 font-medium text-ink"
            >
              Cancelar
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
