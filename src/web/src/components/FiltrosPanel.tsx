import type { Filtros } from '../api/types';

interface FiltrosPanelProps {
  filtros: Filtros;
  onChange: (filtros: Filtros) => void;
  onReset: () => void;
}

const OPCIONES_ESPECIE = [
  { valor: 'perro', etiqueta: 'Perro' },
  { valor: 'gato', etiqueta: 'Gato' },
];

const OPCIONES_TAMANO = [
  { valor: 'pequeño', etiqueta: 'Pequeño' },
  { valor: 'mediano', etiqueta: 'Mediano' },
  { valor: 'grande', etiqueta: 'Grande' },
];

const OPCIONES_ENERGIA = [
  { valor: 'baja', etiqueta: 'Baja' },
  { valor: 'media', etiqueta: 'Media' },
  { valor: 'alta', etiqueta: 'Alta' },
];

const OPCIONES_EDAD = [
  { valor: 'cachorro', etiqueta: 'Cachorro' },
  { valor: 'joven', etiqueta: 'Joven' },
  { valor: 'adulto', etiqueta: 'Adulto' },
  { valor: 'senior', etiqueta: 'Senior' },
];

function alternarValor(lista: string[], valor: string): string[] {
  return lista.includes(valor) ? lista.filter((v) => v !== valor) : [...lista, valor];
}

interface GrupoChipsProps {
  titulo: string;
  opciones: { valor: string; etiqueta: string }[];
  seleccionados: string[];
  campo: keyof Pick<Filtros, 'especie' | 'tamano' | 'energia' | 'edadCategoria'>;
  filtros: Filtros;
  onChange: (filtros: Filtros) => void;
}

function GrupoChips({
  titulo,
  opciones,
  seleccionados,
  campo,
  filtros,
  onChange,
}: GrupoChipsProps) {
  return (
    <div>
      <h3 className="font-mono text-xs tracking-wide text-muted-2 uppercase">{titulo}</h3>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {opciones.map((opcion) => {
          const activo = seleccionados.includes(opcion.valor);
          return (
            <button
              key={opcion.valor}
              type="button"
              aria-pressed={activo}
              onClick={() =>
                onChange({ ...filtros, [campo]: alternarValor(seleccionados, opcion.valor) })
              }
              className={
                activo
                  ? 'rounded-full bg-forest px-3 py-1 text-sm text-bg'
                  : 'rounded-full border border-line bg-surface px-3 py-1 text-sm text-ink-soft hover:border-forest-tint-line'
              }
            >
              {opcion.etiqueta}
            </button>
          );
        })}
      </div>
    </div>
  );
}

interface ToggleConvivenciaProps {
  etiqueta: string;
  activo: boolean;
  campo: keyof Pick<Filtros, 'aptoNinos' | 'aptoPerros' | 'aptoGatos'>;
  filtros: Filtros;
  onChange: (filtros: Filtros) => void;
}

function ToggleConvivencia({ etiqueta, activo, campo, filtros, onChange }: ToggleConvivenciaProps) {
  return (
    <button
      type="button"
      aria-pressed={activo}
      onClick={() => onChange({ ...filtros, [campo]: !activo })}
      className={
        activo
          ? 'rounded-full bg-forest px-3 py-1 text-sm text-bg'
          : 'rounded-full border border-line bg-surface px-3 py-1 text-sm text-ink-soft hover:border-forest-tint-line'
      }
    >
      {etiqueta}
    </button>
  );
}

export function FiltrosPanel({ filtros, onChange, onReset }: FiltrosPanelProps) {
  return (
    <div className="flex flex-col gap-4 rounded-[18px] border border-line bg-surface p-4">
      <GrupoChips
        titulo="Especie"
        opciones={OPCIONES_ESPECIE}
        seleccionados={filtros.especie}
        campo="especie"
        filtros={filtros}
        onChange={onChange}
      />
      <GrupoChips
        titulo="Tamaño"
        opciones={OPCIONES_TAMANO}
        seleccionados={filtros.tamano}
        campo="tamano"
        filtros={filtros}
        onChange={onChange}
      />
      <GrupoChips
        titulo="Nivel de energía"
        opciones={OPCIONES_ENERGIA}
        seleccionados={filtros.energia}
        campo="energia"
        filtros={filtros}
        onChange={onChange}
      />
      <GrupoChips
        titulo="Edad"
        opciones={OPCIONES_EDAD}
        seleccionados={filtros.edadCategoria}
        campo="edadCategoria"
        filtros={filtros}
        onChange={onChange}
      />

      <div>
        <h3 className="font-mono text-xs tracking-wide text-muted-2 uppercase">Convivencia</h3>
        <div className="mt-2 flex flex-wrap gap-1.5">
          <ToggleConvivencia
            etiqueta="Apta con niños"
            activo={filtros.aptoNinos}
            campo="aptoNinos"
            filtros={filtros}
            onChange={onChange}
          />
          <ToggleConvivencia
            etiqueta="Apta con perros"
            activo={filtros.aptoPerros}
            campo="aptoPerros"
            filtros={filtros}
            onChange={onChange}
          />
          <ToggleConvivencia
            etiqueta="Apta con gatos"
            activo={filtros.aptoGatos}
            campo="aptoGatos"
            filtros={filtros}
            onChange={onChange}
          />
        </div>
      </div>

      <div>
        <label
          htmlFor="filtro-distancia"
          className="font-mono text-xs tracking-wide text-muted-2 uppercase"
        >
          Distancia: {filtros.distanciaKm} km
        </label>
        <input
          id="filtro-distancia"
          type="range"
          min={1}
          max={50}
          step={1}
          value={filtros.distanciaKm}
          onChange={(e) => onChange({ ...filtros, distanciaKm: Number(e.target.value) })}
          className="mt-2 w-full accent-forest"
        />
      </div>

      <button
        type="button"
        onClick={onReset}
        className="self-start text-sm font-medium text-forest hover:text-forest-hover"
      >
        Restablecer filtros
      </button>
    </div>
  );
}
