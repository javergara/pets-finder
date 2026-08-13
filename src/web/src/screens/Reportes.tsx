import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { type FiltrosReportes, listarReportesPaginado, obtenerConteos } from '../api/client';
import type { Conteos, Reporte } from '../api/types';
import { ReporteCard } from '../components/ReporteCard';
import { COLORES, TAMANOS, razasPorEspecie } from '../lib/caracteristicas';
import { NOMBRES_ZONAS, ZONA_OTRO } from '../lib/ciudades';

const TODOS = 'todos';
const POR_PAGINA = 12;

export function Reportes() {
  // La franja de la landing enlaza /reportes?estado=reunido (feature 27).
  const [searchParams] = useSearchParams();
  const [estado, setEstado] = useState(
    searchParams.get('estado') === 'reunido' ? 'reunido' : 'activo',
  );
  const [tipo, setTipo] = useState(TODOS);
  const [especie, setEspecie] = useState(TODOS);
  const [zona, setZona] = useState(TODOS);
  const [raza, setRaza] = useState(TODOS);
  const [color, setColor] = useState(TODOS);
  const [tamano, setTamano] = useState(TODOS);
  const [q, setQ] = useState('');
  const [reportes, setReportes] = useState<Reporte[] | null>(null);
  const [total, setTotal] = useState(0);
  const [cargandoMas, setCargandoMas] = useState(false);
  const [conteos, setConteos] = useState<Conteos | null>(null);

  // Prueba social (feature 34): cuántos activos hay por tipo, del backend.
  useEffect(() => {
    obtenerConteos().then(setConteos);
  }, []);

  // La raza depende de la especie elegida: solo se ofrece con perro o gato.
  const razasDisponibles = especie === TODOS ? [] : razasPorEspecie(especie);

  function filtrosActuales(): FiltrosReportes & { q?: string } {
    const filtros: FiltrosReportes & { q?: string } = {};
    if (estado === 'reunido') filtros.estado = 'reunido';
    if (tipo !== TODOS) filtros.tipo = tipo as FiltrosReportes['tipo'];
    if (especie !== TODOS) filtros.especie = especie as FiltrosReportes['especie'];
    if (zona !== TODOS) filtros.zona = zona;
    if (raza !== TODOS) filtros.raza = raza;
    if (color !== TODOS) filtros.color = color;
    if (tamano !== TODOS) filtros.tamano = tamano as FiltrosReportes['tamano'];
    if (q.trim()) filtros.q = q.trim();
    return filtros;
  }

  // Cada cambio de filtro o búsqueda re-consulta la primera página (feature 30:
  // el orden, la exclusión de reunidos y el total los decide la API).
  useEffect(() => {
    listarReportesPaginado(filtrosActuales(), POR_PAGINA, 0).then(({ items, total: t }) => {
      setReportes(items);
      setTotal(t);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estado, tipo, especie, zona, raza, color, tamano, q]);

  async function cargarMas() {
    if (!reportes) return;
    setCargandoMas(true);
    try {
      const { items, total: t } = await listarReportesPaginado(
        filtrosActuales(),
        POR_PAGINA,
        reportes.length,
      );
      setReportes([...reportes, ...items]);
      setTotal(t);
    } finally {
      setCargandoMas(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6 pb-24">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink">Reportes</h1>
          <p className="mt-1 text-sm text-muted">
            Mascotas perdidas y encontradas, las más recientes primero.
            {conteos && (
              <span className="mt-0.5 block">
                Ahora mismo: <strong className="text-danger">{conteos.perdidos} perdidas</strong> ·{' '}
                <strong className="text-forest">{conteos.encontrados} encontradas</strong>
                {reportes && ` · ${total} con estos filtros`}
              </span>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col text-xs text-muted">
            Buscar
            <input
              type="search"
              placeholder="Nombre, señas, barrio…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
            />
          </label>
          <label className="flex flex-col text-xs text-muted">
            Estado
            <select
              value={estado}
              onChange={(e) => setEstado(e.target.value)}
              className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
            >
              <option value="activo">En búsqueda</option>
              <option value="reunido">Reunidas 💚</option>
            </select>
          </label>
          <label className="flex flex-col text-xs text-muted">
            Tipo
            <select
              value={tipo}
              onChange={(e) => setTipo(e.target.value)}
              className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
            >
              <option value={TODOS}>Todos</option>
              <option value="perdido">
                {conteos ? `Perdidas (${conteos.perdidos})` : 'Perdidas'}
              </option>
              <option value="encontrado">
                {conteos ? `Encontradas (${conteos.encontrados})` : 'Encontradas'}
              </option>
            </select>
          </label>
          <label className="flex flex-col text-xs text-muted">
            Especie
            <select
              value={especie}
              onChange={(e) => {
                setEspecie(e.target.value);
                // La raza elegida deja de aplicar al cambiar de especie.
                setRaza(TODOS);
              }}
              className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
            >
              <option value={TODOS}>Todas</option>
              <option value="perro">Perros</option>
              <option value="gato">Gatos</option>
              <option value="otro">Otros</option>
            </select>
          </label>
          {razasDisponibles.length > 0 && (
            <label className="flex flex-col text-xs text-muted">
              Raza
              <select
                value={raza}
                onChange={(e) => setRaza(e.target.value)}
                className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
              >
                <option value={TODOS}>Todas</option>
                {razasDisponibles.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label className="flex flex-col text-xs text-muted">
            Color
            <select
              value={color}
              onChange={(e) => setColor(e.target.value)}
              className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
            >
              <option value={TODOS}>Todos</option>
              {COLORES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col text-xs text-muted">
            Tamaño
            <select
              value={tamano}
              onChange={(e) => setTamano(e.target.value)}
              className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
            >
              <option value={TODOS}>Todos</option>
              {TAMANOS.map((t) => (
                <option key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col text-xs text-muted">
            Zona
            <select
              value={zona}
              onChange={(e) => setZona(e.target.value)}
              className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
            >
              <option value={TODOS}>Todas</option>
              {NOMBRES_ZONAS.map((nombre) => (
                <option key={nombre} value={nombre}>
                  {nombre}
                </option>
              ))}
              <option value={ZONA_OTRO}>Otro lugar</option>
            </select>
          </label>
        </div>
      </header>

      {reportes === null ? (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-80 animate-pulse rounded-[22px] bg-surface-alt" />
          ))}
        </div>
      ) : reportes.length === 0 ? (
        <div className="rounded-2xl border border-line bg-surface p-10 text-center">
          <p className="text-ink-soft">Ningún reporte coincide con estos filtros.</p>
          <Link
            to="/reportar/perdido"
            className="mt-4 inline-block rounded-full bg-forest px-5 py-2 font-medium text-bg"
          >
            Crear el primer reporte
          </Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {reportes.map((reporte) => (
              <ReporteCard key={reporte.id} reporte={reporte} />
            ))}
          </div>
          {reportes.length < total && (
            <div className="text-center">
              <button
                type="button"
                disabled={cargandoMas}
                onClick={cargarMas}
                className="rounded-full border border-line px-6 py-3 font-medium text-ink-soft disabled:opacity-60"
              >
                {cargandoMas ? 'Cargando…' : `Cargar más (${total - reportes.length} restantes)`}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
