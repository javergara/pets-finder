import { useState, type Dispatch, type SetStateAction } from 'react';
import { ApiError, crearNecesidad, cubrirNecesidad } from '../api/client';
import type { CategoriaNecesidad, Necesidad, Organizacion } from '../api/types';
import { mensajeQuieroAyudar, urlWhatsApp } from '../lib/contacto';
import { CATEGORIAS_NECESIDAD, ETIQUETA_CATEGORIA_NECESIDAD } from '../lib/organizaciones';
import { getActiveUserId } from '../lib/session';

type Props = {
  organizacion: Organizacion;
  necesidades: Necesidad[];
  // La lista la carga y la posee `OrganizacionDetalle` (se pide en paralelo con
  // la organización), así que el setter viaja como prop en vez de mudarse aquí.
  onNecesidades: Dispatch<SetStateAction<Necesidad[]>>;
  esAutor: boolean;
};

/**
 * Necesidades de una organización (nació inline en `OrganizacionDetalle`, feature 33).
 *
 * Cualquiera ve la lista y el botón "Quiero ayudar"; solo el autor publica una
 * necesidad nueva o la marca como cubierta — el patrón `esAutor` de toda escritura.
 *
 * Sin necesidades y sin ser el autor no renderiza nada: la sección no tiene qué
 * mostrar ni qué ofrecer.
 */
export function SeccionNecesidades({ organizacion, necesidades, onNecesidades, esAutor }: Props) {
  const [categoriaNueva, setCategoriaNueva] = useState<CategoriaNecesidad>('alimento');
  const [descripcionNueva, setDescripcionNueva] = useState('');
  const [publicando, setPublicando] = useState(false);
  const [errorNecesidad, setErrorNecesidad] = useState<string | null>(null);

  if (necesidades.length === 0 && !esAutor) return null;

  async function publicar() {
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
      onNecesidades((previas) => [nueva, ...previas]);
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
  }

  async function marcarCubierta(necesidadId: number) {
    setErrorNecesidad(null);
    try {
      const cubierta = await cubrirNecesidad(organizacion.id, necesidadId, getActiveUserId());
      onNecesidades((previas) => previas.map((p) => (p.id === cubierta.id ? cubierta : p)));
    } catch (err) {
      setErrorNecesidad(
        err instanceof ApiError
          ? err.message
          : 'No pudimos actualizar la necesidad. Intenta de nuevo.',
      );
    }
  }

  return (
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
                      onClick={() => marcarCubierta(n.id)}
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
            <label htmlFor="necesidad-descripcion" className="text-sm font-medium text-ink-soft">
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
            onClick={publicar}
            className="rounded-full bg-forest px-5 py-2 font-medium text-bg disabled:opacity-60"
          >
            {publicando ? 'Publicando…' : 'Publicar'}
          </button>
        </div>
      )}
      {errorNecesidad && <p className="mt-2 text-sm text-danger">{errorNecesidad}</p>}
    </section>
  );
}
