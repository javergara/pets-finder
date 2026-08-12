import { type FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ApiError, crearReporte } from '../api/client';
import type { Reporte } from '../api/types';
import { FotoUpload } from '../components/FotoUpload';
import { MapaLienzo } from '../components/MapaLienzo';
import { SelectorCiudad } from '../components/SelectorCiudad';
import { COLORES, TAMANOS, razasPorEspecie } from '../lib/caracteristicas';
import { ZONA_OTRO, cajaDeZona } from '../lib/ciudades';
import { getActiveUserId, hasActiveUser } from '../lib/session';

type Props = {
  tipo: 'perdido' | 'encontrado';
};

const COPY = {
  perdido: {
    titulo: 'Perdí a mi mascota',
    intro: 'Cuéntanos cómo es y dónde se perdió. Tu reporte queda visible para quien la encuentre.',
    boton: 'Publicar reporte de perdida',
  },
  encontrado: {
    titulo: 'Encontré una mascota',
    intro:
      'Gracias por ayudar. Describe a la mascota y dónde la viste o la tienes: su familia puede estar buscándola.',
    boton: 'Publicar reporte de encontrada',
  },
} as const;

export function ReportarMascota({ tipo }: Props) {
  const [especie, setEspecie] = useState<'perro' | 'gato' | 'otro'>('perro');
  const [nombreMascota, setNombreMascota] = useState('');
  // Características predefinidas ('' = sin especificar, no se envía).
  const [raza, setRaza] = useState('');
  const [color, setColor] = useState('');
  const [tamano, setTamano] = useState('');
  const [situacion, setSituacion] = useState<'conmigo' | 'vista'>('conmigo');
  const [descripcion, setDescripcion] = useState('');
  // Sin zona preseleccionada: el mapa arranca en la vista nacional y el usuario
  // elige la suya — antes el default "Armenia" producía reportes mal zonificados.
  const [zona, setZona] = useState('');
  const [ciudadTexto, setCiudadTexto] = useState('');
  const [barrio, setBarrio] = useState('');
  const [pin, setPin] = useState(() => {
    const caja = cajaDeZona('');
    return { lat: caja.centroLat, lng: caja.centroLng };
  });
  const [fotoUrl, setFotoUrl] = useState<string | null>(null);
  const [fechaEvento, setFechaEvento] = useState('2026-08-10');
  const [telefono, setTelefono] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [creado, setCreado] = useState<Reporte | null>(null);
  const navigate = useNavigate();

  // Sin registro no hay a quién ligar el reporte: pasar por /registro y volver.
  useEffect(() => {
    if (!hasActiveUser()) {
      navigate(`/registro?volver=/reportar/${tipo}`, { replace: true });
    }
  }, [navigate, tipo]);

  function cambiarZona(zonaNueva: string) {
    setZona(zonaNueva);
    // El pin arranca en el centro del lienzo nuevo; el click lo afina.
    const caja = cajaDeZona(zonaNueva);
    setPin({ lat: caja.centroLat, lng: caja.centroLng });
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!descripcion.trim() || !telefono.trim()) {
      setError('La descripción y el teléfono de contacto son obligatorios.');
      return;
    }
    if (!zona) {
      setError('Selecciona la zona.');
      return;
    }
    if (zona === ZONA_OTRO && !ciudadTexto.trim()) {
      setError('Cuéntanos en qué ciudad o municipio estás.');
      return;
    }

    setError(null);
    setEnviando(true);
    try {
      const reporte = await crearReporte({
        user_id: getActiveUserId(),
        tipo,
        especie,
        nombre_mascota:
          tipo === 'perdido' && nombreMascota.trim() ? nombreMascota.trim() : undefined,
        raza: raza || undefined,
        color: color || undefined,
        tamano: (tamano || undefined) as 'pequeño' | 'mediano' | 'grande' | undefined,
        descripcion: descripcion.trim(),
        foto_url: fotoUrl ?? undefined,
        zona,
        ciudad_texto: zona === ZONA_OTRO ? ciudadTexto.trim() : undefined,
        barrio: barrio.trim() || undefined,
        lat: pin.lat,
        lng: pin.lng,
        situacion: tipo === 'encontrado' ? situacion : undefined,
        fecha_evento: fechaEvento,
        telefono_contacto: telefono.trim(),
      });
      setCreado(reporte);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'No pudimos publicar el reporte. Intenta de nuevo.',
      );
    } finally {
      setEnviando(false);
    }
  }

  if (creado) {
    return (
      <div className="mx-auto mt-12 max-w-md p-6 text-center">
        <h1 className="mb-3 font-display text-3xl text-ink">Reporte publicado</h1>
        <p className="mb-6 text-ink-soft">
          {tipo === 'perdido'
            ? `El reporte de ${
                creado.nombre_mascota ?? 'tu mascota'
              } ya está visible. Mucho ánimo — cada reporte acerca un reencuentro.`
            : 'Tu reporte ya está visible. Gracias por darle una oportunidad de volver a casa.'}
        </p>
        <div className="flex flex-col items-center gap-3">
          <Link to="/reportes" className="rounded-full bg-forest px-6 py-3 font-medium text-bg">
            Ver todos los reportes
          </Link>
          <Link to="/" className="text-sm text-muted">
            Volver al inicio
          </Link>
        </div>
      </div>
    );
  }

  const copy = COPY[tipo];

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <header>
        <h1 className="font-display text-3xl text-ink">{copy.titulo}</h1>
        <p className="mt-1 text-sm text-muted">{copy.intro}</p>
      </header>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div>
          <label htmlFor="reporte-especie" className="text-sm font-medium text-ink-soft">
            ¿Qué animal es?
          </label>
          <select
            id="reporte-especie"
            value={especie}
            onChange={(e) => {
              setEspecie(e.target.value as typeof especie);
              // Las razas dependen de la especie: al cambiarla, la elegida deja de aplicar.
              setRaza('');
            }}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          >
            <option value="perro">Perro</option>
            <option value="gato">Gato</option>
            <option value="otro">Otro</option>
          </select>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          {razasPorEspecie(especie).length > 0 && (
            <div>
              <label htmlFor="reporte-raza" className="text-sm font-medium text-ink-soft">
                Raza
              </label>
              <select
                id="reporte-raza"
                value={raza}
                onChange={(e) => setRaza(e.target.value)}
                className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
              >
                <option value="">No sé / sin especificar</option>
                {razasPorEspecie(especie).map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div>
            <label htmlFor="reporte-color" className="text-sm font-medium text-ink-soft">
              Color
            </label>
            <select
              id="reporte-color"
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
            <label htmlFor="reporte-tamano" className="text-sm font-medium text-ink-soft">
              Tamaño
            </label>
            <select
              id="reporte-tamano"
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

        {tipo === 'perdido' && (
          <div>
            <label htmlFor="reporte-nombre" className="text-sm font-medium text-ink-soft">
              Nombre de tu mascota (opcional)
            </label>
            <input
              id="reporte-nombre"
              type="text"
              value={nombreMascota}
              onChange={(e) => setNombreMascota(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
            />
          </div>
        )}

        {tipo === 'encontrado' && (
          <div>
            <label htmlFor="reporte-situacion" className="text-sm font-medium text-ink-soft">
              ¿Dónde está ahora?
            </label>
            <select
              id="reporte-situacion"
              value={situacion}
              onChange={(e) => setSituacion(e.target.value as typeof situacion)}
              className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
            >
              <option value="conmigo">La tengo conmigo, resguardada</option>
              <option value="vista">La vi pero no pude atraparla</option>
            </select>
          </div>
        )}

        <div>
          <label htmlFor="reporte-descripcion" className="text-sm font-medium text-ink-soft">
            Descripción y señas
          </label>
          <textarea
            id="reporte-descripcion"
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            rows={3}
            placeholder="Color, tamaño, collar, comportamiento…"
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <FotoUpload onFotoSubida={setFotoUrl} />

        <div>
          <label htmlFor="selector-zona" className="text-sm font-medium text-ink-soft">
            ¿En qué zona?
          </label>
          <div className="mt-1">
            <SelectorCiudad
              value={zona}
              onChange={cambiarZona}
              incluirOtro
              placeholder="Selecciona la zona"
            />
          </div>
        </div>

        {zona === ZONA_OTRO && (
          <div>
            <label htmlFor="reporte-ciudad-texto" className="text-sm font-medium text-ink-soft">
              ¿En qué ciudad o municipio?
            </label>
            <input
              id="reporte-ciudad-texto"
              type="text"
              value={ciudadTexto}
              onChange={(e) => setCiudadTexto(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
            />
          </div>
        )}

        <div>
          <p className="text-sm font-medium text-ink-soft">
            {tipo === 'perdido' ? '¿Dónde se perdió?' : '¿Dónde la viste o la encontraste?'}
          </p>
          <p className="mb-2 text-xs text-muted">
            Toca el mapa para poner el pin en el punto aproximado.
          </p>
          <MapaLienzo
            zona={zona}
            onClickCoords={setPin}
            pines={[
              {
                id: 'pin-reporte',
                lat: pin.lat,
                lng: pin.lng,
                colorClass: tipo === 'perdido' ? 'bg-danger' : 'bg-forest',
                etiqueta: 'Ubicación del reporte',
              },
            ]}
          />
        </div>

        <div>
          <label htmlFor="reporte-barrio" className="text-sm font-medium text-ink-soft">
            Barrio o referencia (opcional)
          </label>
          <input
            id="reporte-barrio"
            type="text"
            value={barrio}
            onChange={(e) => setBarrio(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="reporte-fecha" className="text-sm font-medium text-ink-soft">
            {tipo === 'perdido' ? '¿Cuándo se perdió?' : '¿Cuándo la viste?'}
          </label>
          <input
            id="reporte-fecha"
            type="date"
            value={fechaEvento}
            onChange={(e) => setFechaEvento(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="reporte-telefono" className="text-sm font-medium text-ink-soft">
            Teléfono de contacto (WhatsApp)
          </label>
          <input
            id="reporte-telefono"
            type="tel"
            value={telefono}
            onChange={(e) => setTelefono(e.target.value)}
            placeholder="3001234567"
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button
          type="submit"
          disabled={enviando}
          className={`mt-2 rounded-full px-4 py-3 font-medium text-bg disabled:opacity-60 ${
            tipo === 'perdido' ? 'bg-danger' : 'bg-forest'
          }`}
        >
          {enviando ? 'Publicando…' : copy.boton}
        </button>
      </form>
    </div>
  );
}
