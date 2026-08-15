import type { FiltrosMascotas } from '../api/client';
import {
  ENERGIAS,
  ESPECIES_ADOPCION,
  ETIQUETA_ENERGIA,
  ETIQUETA_ESPECIE_ADOPCION,
  ETIQUETA_TAMANO_MASCOTA,
  TAMANOS_MASCOTA,
} from '../lib/adopcion';
import { NOMBRES_ZONAS, ZONA_OTRO } from '../lib/ciudades';

// Filtros del módulo de adopción, compartidos por el catálogo (/adoptar) y —desde
// AD-03— por el deck de descubrimiento: los dos manejan el mismo `FiltrosMascotas`
// exacto, con selección múltiple. No se tocan los filtros inline de /reportes,
// /ayudar y /buscar: aquellos son `<select>` de valor único sobre otros campos y su
// parecido es superficial.
//
// Formato chips con `aria-pressed` (portado de `FiltrosPanel` de la era Adopta) y no
// `<select multiple>`: la multi-selección no cabe en un select usable en móvil, y un
// chip es un target táctil grande. Cada chip lleva su etiqueta completa
// ("Energía baja", no "Baja") porque el título del grupo es decorativo y no está
// asociado al botón: quien navega con lector de pantalla oye solo el nombre del
// botón, y "Baja" a secas no significa nada.
//
// Sin prop de variante: el contenedor decide el layout (aquí `flex flex-wrap` bajo
// el header; en el deck de AD-03, un `aside` lateral). Nada de anchos fijos — a
// 360px los grupos bajan de línea en vez de desbordar la página (feature 16).
//
// ⚠️ No hay grupo de tramo de edad a propósito: `GET /api/pets` recibe
// `edad_categoria` pero todavía lo ignora (su dueño es `services/filtros.py`, que
// llega en AD-03). Un chip que no filtra es peor que un chip ausente. Ese grupo se
// añade aquí en AD-03, con `CATEGORIAS_EDAD` de `lib/adopcion.ts`.

type Props = {
  filtros: FiltrosMascotas;
  onChange: (filtros: FiltrosMascotas) => void;
  onReset: () => void;
};

/** Añade o quita un valor de una selección múltiple, sin mutar la lista. */
function alternar<T extends string>(seleccionados: T[], valor: T): T[] {
  return seleccionados.includes(valor)
    ? seleccionados.filter((v) => v !== valor)
    : [...seleccionados, valor];
}

type GrupoChipsProps<T extends string> = {
  titulo: string;
  opciones: T[];
  etiquetas: Record<T, string>;
  seleccionados: T[];
  onAlternar: (valor: T) => void;
};

function GrupoChips<T extends string>({
  titulo,
  opciones,
  etiquetas,
  seleccionados,
  onAlternar,
}: GrupoChipsProps<T>) {
  return (
    <div>
      <h2 className="font-mono text-xs uppercase tracking-wide text-muted">{titulo}</h2>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {opciones.map((opcion) => {
          const activo = seleccionados.includes(opcion);
          return (
            <button
              key={opcion}
              type="button"
              aria-pressed={activo}
              onClick={() => onAlternar(opcion)}
              className={
                activo
                  ? 'rounded-full bg-forest px-3 py-1.5 text-sm text-bg'
                  : 'rounded-full border border-line bg-surface px-3 py-1.5 text-sm text-ink-soft'
              }
            >
              {etiquetas[opcion]}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function FiltrosAdopcion({ filtros, onChange, onReset }: Props) {
  const hayFiltros =
    filtros.especie.length > 0 ||
    filtros.tamano.length > 0 ||
    filtros.energia.length > 0 ||
    filtros.zona !== '';

  return (
    <div className="flex flex-wrap items-start gap-x-6 gap-y-4">
      <GrupoChips
        titulo="Especie"
        opciones={ESPECIES_ADOPCION}
        etiquetas={ETIQUETA_ESPECIE_ADOPCION}
        seleccionados={filtros.especie}
        onAlternar={(valor) => onChange({ ...filtros, especie: alternar(filtros.especie, valor) })}
      />
      <GrupoChips
        titulo="Tamaño"
        opciones={TAMANOS_MASCOTA}
        etiquetas={ETIQUETA_TAMANO_MASCOTA}
        seleccionados={filtros.tamano}
        onAlternar={(valor) => onChange({ ...filtros, tamano: alternar(filtros.tamano, valor) })}
      />
      <GrupoChips
        titulo="Energía"
        opciones={ENERGIAS}
        etiquetas={ETIQUETA_ENERGIA}
        seleccionados={filtros.energia}
        onAlternar={(valor) => onChange({ ...filtros, energia: alternar(filtros.energia, valor) })}
      />

      {/* La zona es de valor único en toda la app (mismo criterio que el resto de
          pantallas y que el parámetro `zona` de la API): "Todas" = no mandarla. */}
      <label className="flex flex-col text-xs text-muted">
        Zona
        <select
          value={filtros.zona}
          onChange={(e) => onChange({ ...filtros, zona: e.target.value })}
          className="mt-1 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"
        >
          <option value="">Todas las zonas</option>
          {NOMBRES_ZONAS.map((nombre) => (
            <option key={nombre} value={nombre}>
              {nombre}
            </option>
          ))}
          <option value={ZONA_OTRO}>Otro lugar</option>
        </select>
      </label>

      {hayFiltros && (
        <button
          type="button"
          onClick={onReset}
          className="self-center text-sm font-medium text-forest underline-offset-4 hover:underline"
        >
          Limpiar filtros
        </button>
      )}
    </div>
  );
}
