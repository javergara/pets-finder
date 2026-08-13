import { type FormEvent, useState } from 'react';
import { buscarParecidos } from '../api/client';
import type { ConsultaBusqueda, ResultadoBusqueda } from '../api/types';
import { ReporteCard } from '../components/ReporteCard';
import { COLORES, TAMANOS } from '../lib/caracteristicas';
import { NOMBRES_ZONAS, ZONA_OTRO } from '../lib/ciudades';

const ESPECIES = [
  { valor: 'perro', etiqueta: 'Perro' },
  { valor: 'gato', etiqueta: 'Gato' },
  { valor: 'otro', etiqueta: 'Otro animal' },
] as const;

// Busca a tu mascota (feature 38, benchmark encontradogs §9): el dueño la
// describe y el backend rankea por parecido explicable, sin AI. Lo que se
// deja en blanco no se compara.
export function BuscarMascota() {
  const [modo, setModo] = useState<'perdi' | 'encontre'>('perdi');
  const [especie, setEspecie] = useState<ConsultaBusqueda['especie']>('perro');
  const [zona, setZona] = useState('');
  const [color, setColor] = useState('');
  const [tamano, setTamano] = useState('');
  const [senas, setSenas] = useState('');
  const [resultados, setResultados] = useState<ResultadoBusqueda[] | null>(null);
  const [buscando, setBuscando] = useState(false);
  const [error, setError] = useState(false);

  async function buscar(e: FormEvent) {
    e.preventDefault();
    setBuscando(true);
    setError(false);
    try {
      // Perdí la mía → busco entre las encontradas; encontré una → entre las perdidas.
      const encontrados = await buscarParecidos({
        tipo: modo === 'perdi' ? 'encontrado' : 'perdido',
        especie,
        zona: zona || undefined,
        color: color || undefined,
        tamano: tamano || undefined,
        senas: senas || undefined,
      });
      setResultados(encontrados);
    } catch {
      setError(true);
    } finally {
      setBuscando(false);
    }
  }

  const selectClase = 'mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink';

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6 pb-24">
      <header>
        <h1 className="font-display text-3xl text-ink">Busca a tu mascota</h1>
        <p className="mt-1 max-w-xl text-sm text-muted">
          Descríbela como la recuerdas y te mostramos los reportes que más se le parecen. Lo que
          dejes en blanco simplemente no se compara.
        </p>
      </header>

      <form onSubmit={buscar} className="space-y-4 rounded-2xl border border-line bg-surface p-6">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setModo('perdi')}
            className={`rounded-full border px-4 py-2 text-sm font-medium ${
              modo === 'perdi'
                ? 'border-danger bg-danger text-bg'
                : 'border-line bg-surface text-ink-soft'
            }`}
          >
            Perdí la mía
          </button>
          <button
            type="button"
            onClick={() => setModo('encontre')}
            className={`rounded-full border px-4 py-2 text-sm font-medium ${
              modo === 'encontre'
                ? 'border-forest bg-forest text-bg'
                : 'border-line bg-surface text-ink-soft'
            }`}
          >
            Encontré una
          </button>
        </div>

        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col text-xs text-muted">
            Especie
            <select
              value={especie}
              onChange={(e) => setEspecie(e.target.value as ConsultaBusqueda['especie'])}
              className={selectClase}
            >
              {ESPECIES.map((e) => (
                <option key={e.valor} value={e.valor}>
                  {e.etiqueta}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col text-xs text-muted">
            Tamaño
            <select
              value={tamano}
              onChange={(e) => setTamano(e.target.value)}
              className={selectClase}
            >
              <option value="">No sé / cualquiera</option>
              {TAMANOS.map((t) => (
                <option key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col text-xs text-muted">
            Color
            <select
              value={color}
              onChange={(e) => setColor(e.target.value)}
              className={selectClase}
            >
              <option value="">Cualquiera</option>
              {COLORES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col text-xs text-muted">
            Zona
            <select value={zona} onChange={(e) => setZona(e.target.value)} className={selectClase}>
              <option value="">Cualquiera</option>
              {NOMBRES_ZONAS.map((nombre) => (
                <option key={nombre} value={nombre}>
                  {nombre}
                </option>
              ))}
              <option value={ZONA_OTRO}>Otro lugar</option>
            </select>
          </label>
        </div>

        <label className="block text-xs text-muted">
          Señas particulares
          <textarea
            value={senas}
            onChange={(e) => setSenas(e.target.value)}
            rows={2}
            placeholder="Collar rojo, mancha en el ojo, cojera, oreja partida…"
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
          />
          <span className="mt-1 block text-xs text-muted">
            Lo que nadie más podría inventar: es lo que más pesa al comparar.
          </span>
        </label>

        <button
          type="submit"
          disabled={buscando}
          className="w-full rounded-full bg-forest px-6 py-3 font-medium text-bg disabled:opacity-60"
        >
          {buscando ? 'Buscando…' : '🔎 Buscar'}
        </button>
      </form>

      {error && (
        <p className="text-sm text-danger">No pudimos buscar. Intenta de nuevo en un momento.</p>
      )}

      {resultados !== null && !error && (
        <section>
          <h2 className="mb-3 font-display text-lg text-ink">
            {resultados.length === 0
              ? 'Ningún reporte de esa especie por ahora'
              : `${resultados.length} ${
                  resultados.length === 1
                    ? 'reporte parecido'
                    : 'reportes, los más parecidos primero'
                }`}
          </h2>
          {resultados.length === 0 && (
            <p className="text-sm text-muted">
              Vuelve a intentar más tarde — se publican reportes nuevos todo el tiempo.
            </p>
          )}
          <ul className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {resultados.map((r) => (
              <li key={r.id} className="flex flex-col gap-2">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="rounded-full bg-forest px-2.5 py-1 font-mono text-xs text-bg">
                    Se parece en un {r.parecido}%
                  </span>
                  {r.razones.map((razon) => (
                    <span
                      key={razon}
                      className="rounded-full bg-forest-tint px-2 py-0.5 text-xs text-forest"
                    >
                      {razon}
                    </span>
                  ))}
                </div>
                <ReporteCard reporte={r} />
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
