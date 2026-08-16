import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiError, editarOrganizacion, eliminarOrganizacion } from '../api/client';
import type { Organizacion } from '../api/types';
import { getActiveUserId } from '../lib/session';

type Props = {
  organizacion: Organizacion;
  esAutor: boolean;
  // La organización vive en `OrganizacionDetalle` (la comparten todas las
  // secciones), así que editar o cerrar avisa hacia arriba con la versión nueva.
  onActualizada: (organizacion: Organizacion) => void;
};

/**
 * Panel de administración de una organización (nació inline en
 * `OrganizacionDetalle`, features 33 y 32): editar información, cerrar/reabrir
 * y eliminar.
 *
 * Solo lo ve el autor — `esAutor` es el mismo patrón que protege toda escritura
 * en la app; sin él no renderiza nada. El borrado pide confirmación en dos pasos
 * dentro de la propia pantalla (nunca `window.confirm`) y al terminar sale a
 * `/ayudar`, porque la ficha que estabas viendo ya no existe.
 */
export function AdministrarOrganizacion({ organizacion, esAutor, onActualizada }: Props) {
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

  if (!esAutor) return null;

  async function guardarCambios() {
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
      onActualizada(actualizada);
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
    setError(null);
    try {
      onActualizada(
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

  async function eliminar() {
    setEliminando(true);
    try {
      await eliminarOrganizacion(organizacion.id, getActiveUserId());
      navigate('/ayudar');
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'No pudimos eliminar el lugar. Intenta de nuevo.',
      );
      setEliminando(false);
    }
  }

  return (
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
                onClick={eliminar}
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
              Cómo apoyar (Nequi, cuenta, link — opcional)
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
  );
}
