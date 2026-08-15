import { type FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ApiError, editarReporte, mediaUrl, obtenerReporte } from '../api/client';
import type { Reporte } from '../api/types';
import { FotoUpload } from '../components/FotoUpload';
import { MapaLienzo } from '../components/MapaLienzo';
import { COLORES, TAMANOS, razasPorEspecie } from '../lib/caracteristicas';
import { esUsuarioActivo, getActiveUserId } from '../lib/session';

// Edición completa (feature 29): mismos campos del formulario de creación,
// precargados. La zona y la especie no se editan (cambiarían el encuadre y las
// coincidencias — para eso, eliminar y re-crear).
//
// Fix 2026-08-15: la carga iba sin `.catch` (mismo bug que en `ReporteDetalle`),
// así que editar un reporte ya eliminado dejaba el esqueleto para siempre.
const MENSAJE_ERROR_CARGA =
  'No pudimos cargar este reporte. Revisa tu conexión e intenta de nuevo.';

export function EditarReporte() {
  const { id } = useParams<{ id: string }>();
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const [descripcion, setDescripcion] = useState('');
  const [telefono, setTelefono] = useState('');
  const [barrio, setBarrio] = useState('');
  const [fechaEvento, setFechaEvento] = useState('');
  const [raza, setRaza] = useState('');
  const [color, setColor] = useState('');
  const [tamano, setTamano] = useState('');
  const [pin, setPin] = useState<{ lat: number; lng: number } | null>(null);
  const [fotoUrl, setFotoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    setErrorCarga(null);
    obtenerReporte(Number(id))
      .then((r) => {
        // Solo el autor edita; cualquier otro vuelve al detalle.
        if (!esUsuarioActivo(r.user_id)) {
          navigate(`/reporte/${r.id}`, { replace: true });
          return;
        }
        setReporte(r);
        setDescripcion(r.descripcion);
        setTelefono(r.telefono_contacto ?? '');
        setBarrio(r.barrio ?? '');
        setFechaEvento(r.fecha_evento);
        setRaza(r.raza ?? '');
        setColor(r.color ?? '');
        setTamano(r.tamano ?? '');
        setPin({ lat: r.lat, lng: r.lng });
      })
      // El backend responde en español ("El reporte 7 no existe"): copy de
      // producto, se muestra tal cual.
      .catch((err) => setErrorCarga(err instanceof ApiError ? err.message : MENSAJE_ERROR_CARGA));
  }, [id, navigate]);

  if (errorCarga) {
    return (
      <div className="mx-auto max-w-2xl space-y-4 p-6 text-center">
        <h1 className="font-display text-2xl text-ink">No pudimos abrir este reporte</h1>
        <p
          role="alert"
          className="rounded-2xl border border-line bg-surface p-4 text-sm text-ink-soft"
        >
          {errorCarga}
        </p>
        <Link
          to="/reportes"
          className="inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg"
        >
          Ver todos los reportes
        </Link>
      </div>
    );
  }

  if (!reporte) {
    return (
      <div
        role="status"
        aria-label="Cargando el reporte"
        className="mx-auto mt-8 h-96 max-w-2xl animate-pulse rounded-2xl bg-surface-alt"
      />
    );
  }

  const razasDisponibles = razasPorEspecie(reporte.especie);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!reporte) return;
    if (!descripcion.trim() || !telefono.trim()) {
      setError('La descripción y el teléfono de contacto son obligatorios.');
      return;
    }

    setError(null);
    setGuardando(true);
    try {
      await editarReporte(reporte.id, {
        user_id: getActiveUserId(),
        descripcion: descripcion.trim(),
        telefono_contacto: telefono.trim(),
        barrio: barrio.trim() || undefined,
        fecha_evento: fechaEvento,
        raza: raza || undefined,
        color: color || undefined,
        tamano: (tamano || undefined) as 'pequeño' | 'mediano' | 'grande' | undefined,
        lat: pin?.lat,
        lng: pin?.lng,
        foto_url: fotoUrl ?? undefined,
      });
      navigate(`/reporte/${reporte.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'No pudimos guardar los cambios. Intenta de nuevo.',
      );
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl p-6 pb-24">
      <h1 className="mb-2 font-display text-2xl text-ink">
        Editar el reporte de {reporte.nombre_mascota ?? 'la mascota'}
      </h1>
      <p className="mb-6 text-sm text-muted">
        Zona: {reporte.zona === 'Otro' ? reporte.ciudad_texto ?? 'Colombia' : reporte.zona} (no se
        puede cambiar — si la zona está mal, elimina el reporte y créalo de nuevo).
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <span className="text-sm font-medium text-ink-soft">Foto actual</span>
          {reporte.foto_url && !fotoUrl && (
            <img
              src={mediaUrl(reporte.foto_url)}
              alt="Foto actual del reporte"
              className="mt-1 max-h-60 w-full rounded-xl border border-line bg-surface-alt object-contain"
            />
          )}
          <div className="mt-2">
            <FotoUpload onFotoSubida={setFotoUrl} />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {razasDisponibles.length > 0 && (
            <div>
              <label htmlFor="editar-raza" className="text-sm font-medium text-ink-soft">
                Raza
              </label>
              <select
                id="editar-raza"
                value={raza}
                onChange={(e) => setRaza(e.target.value)}
                className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
              >
                <option value="">Sin especificar</option>
                {razasDisponibles.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div>
            <label htmlFor="editar-color" className="text-sm font-medium text-ink-soft">
              Color
            </label>
            <select
              id="editar-color"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
            >
              <option value="">Sin especificar</option>
              {COLORES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="editar-tamano" className="text-sm font-medium text-ink-soft">
              Tamaño
            </label>
            <select
              id="editar-tamano"
              value={tamano}
              onChange={(e) => setTamano(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
            >
              <option value="">Sin especificar</option>
              {TAMANOS.map((t) => (
                <option key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>

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
          <span className="text-sm font-medium text-ink-soft">Ubicación</span>
          <p className="mb-2 mt-0.5 text-xs text-muted">Toca el mapa para corregir el pin.</p>
          <MapaLienzo
            zona={reporte.zona}
            pines={[
              {
                id: reporte.id,
                lat: pin?.lat ?? reporte.lat,
                lng: pin?.lng ?? reporte.lng,
                colorClass: reporte.tipo === 'perdido' ? 'bg-danger' : 'bg-forest',
                etiqueta: 'Ubicación del reporte',
              },
            ]}
            onClickCoords={setPin}
          />
        </div>

        <div>
          <label htmlFor="editar-barrio" className="text-sm font-medium text-ink-soft">
            Barrio (opcional)
          </label>
          <input
            id="editar-barrio"
            type="text"
            value={barrio}
            onChange={(e) => setBarrio(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="editar-fecha" className="text-sm font-medium text-ink-soft">
            {reporte.tipo === 'perdido' ? '¿Cuándo se perdió?' : '¿Cuándo la viste o encontraste?'}
          </label>
          <input
            id="editar-fecha"
            type="date"
            value={fechaEvento}
            onChange={(e) => setFechaEvento(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="editar-telefono" className="text-sm font-medium text-ink-soft">
            Teléfono de contacto (WhatsApp)
          </label>
          <input
            id="editar-telefono"
            type="tel"
            value={telefono}
            onChange={(e) => setTelefono(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={guardando}
            className="rounded-full bg-forest px-5 py-3 font-medium text-bg disabled:opacity-60"
          >
            {guardando ? 'Guardando…' : 'Guardar cambios'}
          </button>
          <button
            type="button"
            onClick={() => navigate(`/reporte/${reporte.id}`)}
            className="rounded-full border border-line px-5 py-3 font-medium text-ink-soft"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
