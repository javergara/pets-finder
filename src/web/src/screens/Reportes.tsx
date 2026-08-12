import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { type FiltrosReportes, listarReportes } from '../api/client';
import type { Reporte } from '../api/types';
import { ReporteCard } from '../components/ReporteCard';
import { NOMBRES_ZONAS, ZONA_OTRO } from '../lib/ciudades';

const TODOS = 'todos';

export function Reportes() {
  const [tipo, setTipo] = useState(TODOS);
  const [especie, setEspecie] = useState(TODOS);
  const [zona, setZona] = useState(TODOS);
  const [reportes, setReportes] = useState<Reporte[] | null>(null);

  // Cada cambio de filtro re-consulta al backend (el orden y la exclusión de
  // reunidos los decide la API, no el cliente).
  useEffect(() => {
    const filtros: FiltrosReportes = {};
    if (tipo !== TODOS) filtros.tipo = tipo as FiltrosReportes['tipo'];
    if (especie !== TODOS) filtros.especie = especie as FiltrosReportes['especie'];
    if (zona !== TODOS) filtros.zona = zona;
    listarReportes(filtros).then(setReportes);
  }, [tipo, especie, zona]);

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6 pb-24">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink">Reportes</h1>
          <p className="mt-1 text-sm text-muted">
            Mascotas perdidas y encontradas, las más recientes primero.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col text-xs text-muted">
            Tipo
            <select
              value={tipo}
              onChange={(e) => setTipo(e.target.value)}
              className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
            >
              <option value={TODOS}>Todos</option>
              <option value="perdido">Perdidas</option>
              <option value="encontrado">Encontradas</option>
            </select>
          </label>
          <label className="flex flex-col text-xs text-muted">
            Especie
            <select
              value={especie}
              onChange={(e) => setEspecie(e.target.value)}
              className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
            >
              <option value={TODOS}>Todas</option>
              <option value="perro">Perros</option>
              <option value="gato">Gatos</option>
              <option value="otro">Otros</option>
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
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {reportes.map((reporte) => (
            <ReporteCard key={reporte.id} reporte={reporte} />
          ))}
        </div>
      )}
    </div>
  );
}
