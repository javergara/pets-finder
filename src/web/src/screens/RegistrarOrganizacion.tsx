import { type FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ApiError, crearOrganizacion } from '../api/client';
import type { Organizacion, TipoOrganizacion } from '../api/types';
import { FotoUpload } from '../components/FotoUpload';
import { MapaLienzo } from '../components/MapaLienzo';
import { SelectorCiudad } from '../components/SelectorCiudad';
import { ZONA_OTRO, cajaDeZona } from '../lib/ciudades';
import { ETIQUETA_TIPO_ORGANIZACION, TIPOS_ORGANIZACION } from '../lib/organizaciones';
import { getActiveUserId, hasActiveUser } from '../lib/session';
import { AvisoSeguridad } from '../components/AvisoSeguridad';

export function RegistrarOrganizacion() {
  const [tipo, setTipo] = useState<TipoOrganizacion>('centro_acopio');
  const [nombre, setNombre] = useState('');
  const [descripcion, setDescripcion] = useState('');
  // Sin zona preseleccionada (igual que reportar): vista nacional hasta elegir.
  const [zona, setZona] = useState('');
  const [ciudadTexto, setCiudadTexto] = useState('');
  const [barrio, setBarrio] = useState('');
  const [direccion, setDireccion] = useState('');
  const [pin, setPin] = useState(() => {
    const caja = cajaDeZona('');
    return { lat: caja.centroLat, lng: caja.centroLng };
  });
  const [telefono, setTelefono] = useState('');
  const [horario, setHorario] = useState('');
  const [comoDonar, setComoDonar] = useState('');
  const [fotoUrl, setFotoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [creada, setCreada] = useState<Organizacion | null>(null);
  const navigate = useNavigate();

  // Sin registro no hay autor que pueda editar/cerrar el lugar después.
  useEffect(() => {
    if (!hasActiveUser()) {
      navigate('/registro?volver=/ayudar/registrar', { replace: true });
    }
  }, [navigate]);

  function cambiarZona(zonaNueva: string) {
    setZona(zonaNueva);
    const caja = cajaDeZona(zonaNueva);
    setPin({ lat: caja.centroLat, lng: caja.centroLng });
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!nombre.trim() || !descripcion.trim() || !direccion.trim() || !telefono.trim()) {
      setError('Nombre, descripción, dirección y teléfono son obligatorios.');
      return;
    }
    if (!zona) {
      setError('Selecciona la zona.');
      return;
    }
    if (zona === ZONA_OTRO && !ciudadTexto.trim()) {
      setError('Cuéntanos en qué ciudad o municipio está.');
      return;
    }

    setError(null);
    setEnviando(true);
    try {
      const organizacion = await crearOrganizacion({
        user_id: getActiveUserId(),
        tipo,
        nombre: nombre.trim(),
        descripcion: descripcion.trim(),
        zona,
        ciudad_texto: zona === ZONA_OTRO ? ciudadTexto.trim() : undefined,
        barrio: barrio.trim() || undefined,
        direccion: direccion.trim(),
        lat: pin.lat,
        lng: pin.lng,
        telefono_contacto: telefono.trim(),
        horario: horario.trim() || undefined,
        como_donar: comoDonar.trim() || undefined,
        foto_url: fotoUrl ?? undefined,
      });
      setCreada(organizacion);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'No pudimos registrar el lugar. Intenta de nuevo.',
      );
    } finally {
      setEnviando(false);
    }
  }

  if (creada) {
    return (
      <div className="mx-auto mt-8 max-w-md space-y-4 p-6 text-center">
        <h1 className="font-display text-2xl text-ink">¡Lugar registrado! 💚</h1>
        <p className="text-sm text-ink-soft">
          {creada.nombre} ya aparece en la red de apoyo para que más gente lo encuentre.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link
            to={`/organizacion/${creada.id}`}
            className="rounded-full bg-forest px-5 py-3 font-medium text-bg"
          >
            Ver su página
          </Link>
          <Link
            to="/ayudar"
            className="rounded-full border border-line px-5 py-3 font-medium text-ink"
          >
            Ir a los centros de ayuda
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl p-6 pb-24">
      <h1 className="mb-2 font-display text-2xl text-ink">Registrar un lugar de apoyo</h1>
      <p className="mb-6 text-sm text-muted">
        Centros de acopio, fundaciones, tiendas o veterinarias que estén ayudando. Quedará visible
        en el mapa y el directorio de la red de apoyo.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label htmlFor="registrar-tipo" className="text-sm font-medium text-ink-soft">
            Tipo de lugar
          </label>
          <select
            id="registrar-tipo"
            value={tipo}
            onChange={(e) => setTipo(e.target.value as TipoOrganizacion)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          >
            {TIPOS_ORGANIZACION.map((t) => (
              <option key={t} value={t}>
                {ETIQUETA_TIPO_ORGANIZACION[t].texto}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="registrar-nombre" className="text-sm font-medium text-ink-soft">
            Nombre
          </label>
          <input
            id="registrar-nombre"
            type="text"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="registrar-descripcion" className="text-sm font-medium text-ink-soft">
            Qué hacen / qué reciben
          </label>
          <textarea
            id="registrar-descripcion"
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            rows={3}
            placeholder="Ej: recibimos alimento, cobijas y medicinas; damos hogar de paso"
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="registrar-zona" className="text-sm font-medium text-ink-soft">
            Zona
          </label>
          <div className="mt-1">
            <SelectorCiudad
              id="registrar-zona"
              value={zona}
              onChange={cambiarZona}
              incluirOtro
              placeholder="Selecciona la zona"
            />
          </div>
        </div>

        {zona === ZONA_OTRO && (
          <div>
            <label htmlFor="registrar-ciudad" className="text-sm font-medium text-ink-soft">
              ¿En qué ciudad o municipio?
            </label>
            <input
              id="registrar-ciudad"
              type="text"
              value={ciudadTexto}
              onChange={(e) => setCiudadTexto(e.target.value)}
              className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
            />
          </div>
        )}

        <div>
          <span className="text-sm font-medium text-ink-soft">Ubicación en el mapa</span>
          <p className="mb-2 mt-0.5 text-xs text-muted">Toca el punto donde queda.</p>
          <MapaLienzo
            zona={zona}
            pines={[
              {
                id: 1,
                lat: pin.lat,
                lng: pin.lng,
                colorClass: ETIQUETA_TIPO_ORGANIZACION[tipo].color,
                etiqueta: 'Ubicación del lugar',
              },
            ]}
            onClickCoords={setPin}
          />
        </div>

        <div>
          <label htmlFor="registrar-direccion" className="text-sm font-medium text-ink-soft">
            Dirección
          </label>
          <input
            id="registrar-direccion"
            type="text"
            placeholder="Ej: Cra 14 #10-25"
            value={direccion}
            onChange={(e) => setDireccion(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="registrar-barrio" className="text-sm font-medium text-ink-soft">
            Barrio (opcional)
          </label>
          <input
            id="registrar-barrio"
            type="text"
            value={barrio}
            onChange={(e) => setBarrio(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="registrar-telefono" className="text-sm font-medium text-ink-soft">
            Teléfono / WhatsApp
          </label>
          <input
            id="registrar-telefono"
            type="tel"
            value={telefono}
            onChange={(e) => setTelefono(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="registrar-horario" className="text-sm font-medium text-ink-soft">
            Horario (opcional)
          </label>
          <input
            id="registrar-horario"
            type="text"
            placeholder="Ej: Lun-Sáb 8am-5pm"
            value={horario}
            onChange={(e) => setHorario(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="registrar-donar" className="text-sm font-medium text-ink-soft">
            Cómo donar (opcional — Nequi, cuenta, link)
          </label>
          <input
            id="registrar-donar"
            type="text"
            value={comoDonar}
            onChange={(e) => setComoDonar(e.target.value)}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <FotoUpload onFotoSubida={setFotoUrl} />

        {error && <p className="text-sm text-danger">{error}</p>}

        <AvisoSeguridad contexto="publicar" />

        <button
          type="submit"
          disabled={enviando}
          className="mt-2 rounded-full bg-forest px-4 py-3 font-medium text-bg disabled:opacity-60"
        >
          {enviando ? 'Registrando…' : 'Registrar lugar'}
        </button>
      </form>
    </div>
  );
}
