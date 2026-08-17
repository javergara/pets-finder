import { useState } from 'react';
import type { FiltrosMascotas } from '../api/client';
import {
  CATEGORIAS_EDAD,
  contarFiltrosActivos,
  ENERGIAS,
  ESPECIES_ADOPCION,
  ETIQUETA_CATEGORIA_EDAD,
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
// Desde AD-08 el panel se **pliega en móvil** y el plegado vive aquí, no en cada
// pantalla: el catálogo y el deck lo usan igual y una segunda copia se
// desincronizaría (ya pasó con la cuenta de filtros activos, ver
// `contarFiltrosActivos`). Medido sobre el código: con los cuatro grupos de
// chips desplegados, la rejilla del catálogo empieza cerca de los 800px y la
// carta del deck sobre los 590 — con un viewport de 360×640 no se ve ni una
// mascota sin hacer scroll, que es lo primero que necesita ver quien entra.
//
// ⚠️ **El panel se DESMONTA al plegarse; no se esconde con CSS.** Un
// `class="hidden"` sería invisible para los tests (jsdom no aplica CSS, así que
// el chip seguiría siendo pulsable en el test y estaría a la vista en el móvil
// real si la clase fuera mal), y además dejaría los chips en el orden de foco
// del teclado estando ocultos.
//
// ⚠️ **El estado inicial se decide con `matchMedia` y a la defensiva**: jsdom
// (29.1.1) **no implementa `window.matchMedia`** —llamarlo lanza `window.
// matchMedia is not a function`—, así que la comprobación de `typeof` no es
// ceremonia: sin ella los tests de las dos pantallas revientan al montar. En
// jsdom el resultado es `false` → plegado, que es justo el caso móvil que hay
// que proteger; en Chrome a ≥1024px da `true` y el `aside` pegajoso del deck se
// pinta desplegado como siempre. No se lee un tamaño de ventana ni se escucha el
// resize: una consulta al montar basta y no hay estado que mantener en sincronía.
//
// El grupo de tramo de edad se añadió en AD-03, cuando `GET /api/pets` empezó a
// traducir `edad_categoria` a SQL (`services/filtros.py`): antes el backend
// recibía el param y lo ignoraba, y un chip que no filtra es peor que un chip
// ausente. Los tramos no se declaran aquí — salen de `CATEGORIAS_EDAD` de
// `lib/adopcion.ts`, que comparte cortes con `EDAD_CATEGORIA_RANGOS`.

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

/** Ancho a partir del cual el panel nace desplegado: el mismo `lg` de Tailwind
 * con el que el botón se esconde y con el que el deck pasa a columna lateral. */
const CONSULTA_ESCRITORIO = '(min-width: 1024px)';

export function FiltrosAdopcion({ filtros, onChange, onReset }: Props) {
  const activos = contarFiltrosActivos(filtros);
  const hayFiltros = activos > 0;
  // Ver la cabecera: el `typeof` protege de jsdom, que no trae `matchMedia`.
  const [abierto, setAbierto] = useState(
    () => typeof window.matchMedia === 'function' && window.matchMedia(CONSULTA_ESCRITORIO).matches,
  );

  return (
    <div>
      {/* Solo en móvil: en escritorio sobra el pliegue y los filtros se ven
          enteros. El contador es obligatorio, no adorno — con el panel cerrado
          es la única pista de que el listado está recortado. */}
      <button
        type="button"
        onClick={() => setAbierto((previo) => !previo)}
        aria-expanded={abierto}
        aria-controls="filtros-adopcion"
        className="rounded-full border border-line bg-surface px-4 py-2 text-sm font-medium text-ink-soft lg:hidden"
      >
        {hayFiltros ? `Filtros · ${activos}` : 'Filtros'}
      </button>

      {abierto && (
        <div
          id="filtros-adopcion"
          className="mt-3 flex flex-wrap items-start gap-x-6 gap-y-4 lg:mt-0"
        >
          <GrupoChips
            titulo="Especie"
            opciones={ESPECIES_ADOPCION}
            etiquetas={ETIQUETA_ESPECIE_ADOPCION}
            seleccionados={filtros.especie}
            onAlternar={(valor) =>
              onChange({ ...filtros, especie: alternar(filtros.especie, valor) })
            }
          />
          <GrupoChips
            titulo="Tamaño"
            opciones={TAMANOS_MASCOTA}
            etiquetas={ETIQUETA_TAMANO_MASCOTA}
            seleccionados={filtros.tamano}
            onAlternar={(valor) =>
              onChange({ ...filtros, tamano: alternar(filtros.tamano, valor) })
            }
          />
          <GrupoChips
            titulo="Energía"
            opciones={ENERGIAS}
            etiquetas={ETIQUETA_ENERGIA}
            seleccionados={filtros.energia}
            onAlternar={(valor) =>
              onChange({ ...filtros, energia: alternar(filtros.energia, valor) })
            }
          />
          <GrupoChips
            titulo="Edad"
            opciones={CATEGORIAS_EDAD}
            etiquetas={ETIQUETA_CATEGORIA_EDAD}
            seleccionados={filtros.edad}
            onAlternar={(valor) => onChange({ ...filtros, edad: alternar(filtros.edad, valor) })}
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
      )}
    </div>
  );
}
