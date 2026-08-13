import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listarReportes } from '../api/client';
import type { Reporte } from '../api/types';
import { MapaLienzo, type PinMapa } from '../components/MapaLienzo';
import { NOMBRES_ZONAS } from '../lib/ciudades';

// Valor especial del selector: no es una zona de reporte, es la vista agregada
// sobre el lienzo nacional (lib/ciudades.ts::cajaDeZona la resuelve a COLOMBIA).
const VISTA_COLOMBIA = 'Colombia';

const ETIQUETA_ESPECIE = { perro: 'Perro', gato: 'Gato', otro: 'Otro animal' } as const;

export function MapaReportes() {
  const [vista, setVista] = useState(VISTA_COLOMBIA);
  const [soloReunidos, setSoloReunidos] = useState(false);
  const [reportes, setReportes] = useState<Reporte[]>([]);
  const [seleccionado, setSeleccionado] = useState<Reporte | null>(null);

  // Siempre se piden todos (activos, o solo reunidos con la capa 💚): en la
  // vista de una zona se filtra en memoria (los "Otro" solo aparecen en la
  // vista nacional, donde su pin cae en su coordenada real).
  useEffect(() => {
    listarReportes(soloReunidos ? { estado: 'reunido' } : {}).then(setReportes);
    setSeleccionado(null);
  }, [soloReunidos]);

  const visibles = vista === VISTA_COLOMBIA ? reportes : reportes.filter((r) => r.zona === vista);

  const pines: PinMapa[] = visibles.map((reporte) => ({
    id: reporte.id,
    lat: reporte.lat,
    lng: reporte.lng,
    colorClass: reporte.tipo === 'perdido' && !soloReunidos ? 'bg-danger' : 'bg-forest',
    etiqueta: `Reporte: ${reporte.nombre_mascota ?? ETIQUETA_ESPECIE[reporte.especie]}`,
    onClick: () => setSeleccionado(reporte),
  }));

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6 pb-24">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink">Mapa de reportes</h1>
          <p className="mt-1 text-sm text-muted">
            {visibles.length} {soloReunidos ? 'reencuentros' : 'reportes activos'} en{' '}
            {vista === VISTA_COLOMBIA ? 'todo Colombia' : vista}.
          </p>
          <label className="mt-2 flex items-center gap-2 text-sm text-ink-soft">
            <input
              type="checkbox"
              checked={soloReunidos}
              onChange={(e) => setSoloReunidos(e.target.checked)}
              className="accent-forest"
            />
            Solo reencuentros 💚
          </label>
        </div>
        <label className="flex flex-col text-xs text-muted">
          Zona
          <select
            value={vista}
            onChange={(e) => {
              setVista(e.target.value);
              setSeleccionado(null);
            }}
            className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
          >
            <option value={VISTA_COLOMBIA}>Todo Colombia</option>
            {NOMBRES_ZONAS.map((nombre) => (
              <option key={nombre} value={nombre}>
                {nombre}
              </option>
            ))}
          </select>
        </label>
      </header>

      <MapaLienzo zona={vista} pines={pines} />

      <div className="flex flex-wrap items-center gap-5 text-sm text-ink-soft">
        <span className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-danger" aria-hidden />
          Mascota perdida
        </span>
        <span className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-forest" aria-hidden />
          Mascota encontrada
        </span>
      </div>

      {seleccionado && (
        <div className="flex items-center justify-between gap-4 rounded-2xl border border-line bg-surface p-4">
          <div>
            <p className="font-display text-lg text-ink">
              {seleccionado.nombre_mascota ?? ETIQUETA_ESPECIE[seleccionado.especie]}
            </p>
            <p className="text-sm text-muted">
              {seleccionado.tipo === 'perdido' ? 'Se perdió' : 'Encontrada'} ·{' '}
              {seleccionado.zona === 'Otro'
                ? seleccionado.ciudad_texto ?? 'Colombia'
                : seleccionado.zona}
            </p>
          </div>
          <Link
            to={`/reporte/${seleccionado.id}`}
            className="rounded-full bg-forest px-4 py-2 text-sm font-medium text-bg"
          >
            Ver reporte
          </Link>
        </div>
      )}
    </div>
  );
}
