import { type FormEvent, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ApiError, crearAvisoAyuda } from '../api/client';
import type { CategoriaAvisoAyuda, TipoAvisoAyuda } from '../api/types';
import { AvisoSeguridad } from '../components/AvisoSeguridad';
import { CATEGORIAS_AVISO, ETIQUETA_CATEGORIA_AVISO } from '../lib/avisos';
import { NOMBRES_ZONAS, ZONA_OTRO } from '../lib/ciudades';
import { getActiveUserId, hasActiveUser } from '../lib/session';
import { Navigate } from 'react-router-dom';

// Publicar un aviso de ayuda entre personas (feature 42, Patas en Cali §10).
export function PublicarAvisoAyuda() {
  const [busqueda] = useSearchParams();
  const inicial = busqueda.get('tipo') === 'ofrezco' ? 'ofrezco' : 'pido';
  const [tipo, setTipo] = useState<TipoAvisoAyuda>(inicial);
  const [categoria, setCategoria] = useState<CategoriaAvisoAyuda>('hogar_de_paso');
  const [titulo, setTitulo] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [zona, setZona] = useState('');
  const [ciudadTexto, setCiudadTexto] = useState('');
  const [barrio, setBarrio] = useState('');
  const [telefono, setTelefono] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Mismo gate de cuenta liviana que reportar (feature 04).
  if (!hasActiveUser()) {
    return <Navigate to={`/registro?volver=${encodeURIComponent('/ayudar/publicar-aviso')}`} />;
  }

  async function enviar(e: FormEvent) {
    e.preventDefault();
    if (!titulo.trim() || !descripcion.trim() || !telefono.trim() || !zona) {
      setError('Completa el título, la descripción, la zona y tu teléfono.');
      return;
    }
    if (zona === ZONA_OTRO && !ciudadTexto.trim()) {
      setError('Con "Otro lugar" cuéntanos en qué ciudad.');
      return;
    }
    setError(null);
    setEnviando(true);
    try {
      await crearAvisoAyuda({
        user_id: getActiveUserId(),
        tipo,
        categoria,
        titulo: titulo.trim(),
        descripcion: descripcion.trim(),
        zona,
        ...(zona === ZONA_OTRO ? { ciudad_texto: ciudadTexto.trim() } : {}),
        ...(barrio.trim() ? { barrio: barrio.trim() } : {}),
        telefono_contacto: telefono.trim(),
      });
      navigate('/ayudar?tab=comunidad');
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'No pudimos publicar el aviso. Intenta de nuevo.',
      );
    } finally {
      setEnviando(false);
    }
  }

  const inputClase = 'mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink';

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6 pb-24">
      <header>
        <h1 className="font-display text-3xl text-ink">
          {tipo === 'pido' ? 'Necesito ayuda' : 'Quiero ayudar'}
        </h1>
        <p className="mt-1 text-sm text-muted">
          {tipo === 'pido'
            ? 'Cuenta qué necesitas: rescate, salud, alimento, hogar de paso…'
            : 'Ofrece lo que puedas: tu casa como hogar de paso, transporte, comida…'}
        </p>
      </header>

      <form onSubmit={enviar} className="space-y-4 rounded-2xl border border-line bg-surface p-6">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setTipo('pido')}
            className={`rounded-full border px-4 py-2 text-sm font-medium ${
              tipo === 'pido'
                ? 'border-danger bg-danger text-bg'
                : 'border-line bg-surface text-ink-soft'
            }`}
          >
            Necesito ayuda
          </button>
          <button
            type="button"
            onClick={() => setTipo('ofrezco')}
            className={`rounded-full border px-4 py-2 text-sm font-medium ${
              tipo === 'ofrezco'
                ? 'border-forest bg-forest text-bg'
                : 'border-line bg-surface text-ink-soft'
            }`}
          >
            Ofrezco ayuda
          </button>
        </div>

        <div>
          <label htmlFor="aviso-categoria" className="text-sm font-medium text-ink-soft">
            Categoría
          </label>
          <select
            id="aviso-categoria"
            value={categoria}
            onChange={(e) => setCategoria(e.target.value as CategoriaAvisoAyuda)}
            className={inputClase}
          >
            {CATEGORIAS_AVISO.map((c) => (
              <option key={c} value={c}>
                {ETIQUETA_CATEGORIA_AVISO[c]}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="aviso-titulo" className="text-sm font-medium text-ink-soft">
            Título breve
          </label>
          <input
            id="aviso-titulo"
            type="text"
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            placeholder={
              tipo === 'pido'
                ? 'Ej: Necesito comida para 10 gatos rescatados'
                : 'Ej: Ofrezco mi casa como hogar de paso'
            }
            className={inputClase}
          />
        </div>

        <div>
          <label htmlFor="aviso-descripcion" className="text-sm font-medium text-ink-soft">
            Descripción
          </label>
          <textarea
            id="aviso-descripcion"
            rows={3}
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            placeholder="Cuéntanos los detalles: cuántos animales, desde cuándo, qué necesitas o qué ofreces…"
            className={inputClase}
          />
        </div>

        <div className="flex flex-wrap gap-3">
          <div className="min-w-[10rem] flex-1">
            <label htmlFor="aviso-zona" className="text-sm font-medium text-ink-soft">
              Zona
            </label>
            <select
              id="aviso-zona"
              value={zona}
              onChange={(e) => setZona(e.target.value)}
              className={inputClase}
            >
              <option value="">Selecciona la zona</option>
              {NOMBRES_ZONAS.map((nombre) => (
                <option key={nombre} value={nombre}>
                  {nombre}
                </option>
              ))}
              <option value={ZONA_OTRO}>Otro lugar de Colombia</option>
            </select>
          </div>
          {zona === ZONA_OTRO && (
            <div className="min-w-[10rem] flex-1">
              <label htmlFor="aviso-ciudad" className="text-sm font-medium text-ink-soft">
                ¿En qué ciudad?
              </label>
              <input
                id="aviso-ciudad"
                type="text"
                value={ciudadTexto}
                onChange={(e) => setCiudadTexto(e.target.value)}
                className={inputClase}
              />
            </div>
          )}
          <div className="min-w-[10rem] flex-1">
            <label htmlFor="aviso-barrio" className="text-sm font-medium text-ink-soft">
              Barrio o referencia (opcional)
            </label>
            <input
              id="aviso-barrio"
              type="text"
              value={barrio}
              onChange={(e) => setBarrio(e.target.value)}
              className={inputClase}
            />
          </div>
        </div>

        <div>
          <label htmlFor="aviso-telefono" className="text-sm font-medium text-ink-soft">
            Teléfono de contacto (WhatsApp)
          </label>
          <input
            id="aviso-telefono"
            type="tel"
            value={telefono}
            onChange={(e) => setTelefono(e.target.value)}
            placeholder="3001234567"
            className={inputClase}
          />
        </div>

        <AvisoSeguridad contexto="publicar" />

        {error && <p className="text-sm text-danger">{error}</p>}

        <button
          type="submit"
          disabled={enviando}
          className="w-full rounded-full bg-forest px-6 py-3 font-medium text-bg disabled:opacity-60"
        >
          {enviando ? 'Publicando…' : 'Publicar aviso'}
        </button>
      </form>
    </div>
  );
}
