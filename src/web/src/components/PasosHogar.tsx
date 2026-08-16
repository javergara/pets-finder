import type { Dispatch, SetStateAction } from 'react';
import {
  ETIQUETA_ENERGIA,
  ETIQUETA_ESPECIE_ADOPCION,
  ETIQUETA_TAMANO_MASCOTA,
} from '../lib/adopcion';
import {
  ETIQUETA_ESPACIO,
  ETIQUETA_EXPERIENCIA,
  ETIQUETA_VIVIENDA,
  type EstadoWizard,
  alternar,
} from '../lib/hogar';
import { GrupoOpciones } from './GrupoOpciones';
import { OpcionCard, OpcionesSiNo } from './OpcionCard';

// Las preguntas del cuestionario de hogar (AD-04): catálogos, validación por
// paso y el JSX de cada uno.
//
// Están aquí y no en `screens/CuestionarioHogar.tsx` porque son dos cosas
// distintas y juntas pasaban de 400 líneas: **esto es el formulario** (qué se
// pregunta y cuándo está contestado) y la pantalla es **el flujo** (gate de
// cuenta, precarga, guardado y navegación). Se prueban desde el test de la
// pantalla, que es donde tienen sentido: un paso suelto no significa nada.

type CampoNumeroProps = {
  id: string;
  etiqueta: string;
  ayuda?: string;
  valor: number | null;
  onChange: (valor: number | null) => void;
  min?: number;
  max?: number;
};

// Local a propósito: un solo uso real en toda la app (`GrupoOpciones` y
// `OpcionCard` sí se comparten porque los usa también `PublicarMascota`).
function CampoNumero({ id, etiqueta, ayuda, valor, onChange, min = 0, max }: CampoNumeroProps) {
  return (
    <div>
      <label htmlFor={id} className="font-display text-lg text-ink">
        {etiqueta}
      </label>
      {ayuda && <p className="mt-1 text-sm text-ink-soft">{ayuda}</p>}
      <input
        id={id}
        type="number"
        inputMode="numeric"
        min={min}
        max={max}
        value={valor ?? ''}
        // Vacío es `null` ("no lo digo"), no 0: `Number('')` es 0 y guardaría un
        // presupuesto de cero pesos que nadie declaró.
        onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
        className="mt-2 w-full rounded-xl border border-line bg-surface px-3 py-3 text-ink"
      />
    </div>
  );
}

type GrupoMultipleProps<T extends string> = {
  titulo: string;
  etiquetas: Record<T, string>;
  valores: T[];
  onChange: (valores: T[]) => void;
};

function GrupoMultiple<T extends string>({
  titulo,
  etiquetas,
  valores,
  onChange,
}: GrupoMultipleProps<T>) {
  return (
    <div>
      <h2 className="mb-2 font-display text-lg text-ink">{titulo}</h2>
      <div role="group" aria-label={titulo} className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {(Object.entries(etiquetas) as [T, string][]).map(([opcion, etiqueta]) => (
          <OpcionCard
            key={opcion}
            etiqueta={etiqueta}
            seleccionada={valores.includes(opcion)}
            onClick={() => onChange(alternar(valores, opcion))}
          />
        ))}
      </div>
    </div>
  );
}

type PasosHogarProps = {
  paso: number;
  estado: EstadoWizard;
  setEstado: Dispatch<SetStateAction<EstadoWizard>>;
};

export function PasosHogar({ paso, estado, setEstado }: PasosHogarProps) {
  return (
    <div className="mt-6 flex flex-col gap-6">
      {paso === 1 && (
        <>
          <GrupoOpciones
            titulo="¿Dónde vives?"
            etiquetas={ETIQUETA_VIVIENDA}
            valor={estado.vivienda}
            onChange={(vivienda) => setEstado((s) => ({ ...s, vivienda }))}
          />
          <GrupoOpciones
            titulo="¿Tienes espacio exterior?"
            etiquetas={ETIQUETA_ESPACIO}
            valor={estado.espacio_exterior}
            onChange={(espacio_exterior) => setEstado((s) => ({ ...s, espacio_exterior }))}
          />
        </>
      )}

      {paso === 2 && (
        <>
          <CampoNumero
            id="hogar-personas"
            etiqueta="¿Cuántas personas viven en tu hogar?"
            valor={estado.personas_en_casa}
            min={1}
            onChange={(valor) => setEstado((s) => ({ ...s, personas_en_casa: valor ?? 1 }))}
          />
          <div>
            <h2 className="mb-2 font-display text-lg text-ink">¿Hay niños en casa?</h2>
            <OpcionesSiNo
              etiqueta="¿Hay niños en casa?"
              valor={estado.tiene_ninos}
              onChange={(tiene_ninos) => setEstado((s) => ({ ...s, tiene_ninos }))}
            />
          </div>
        </>
      )}

      {paso === 3 && (
        <CampoNumero
          id="hogar-horas"
          etiqueta="¿Cuántas horas pasas fuera de casa al día?"
          ayuda="Es lo que más pesa: una mascota de mucha energía sola diez horas lo pasa mal."
          valor={estado.horas_fuera_dia}
          min={0}
          max={24}
          onChange={(valor) => setEstado((s) => ({ ...s, horas_fuera_dia: valor ?? 0 }))}
        />
      )}

      {paso === 4 && (
        <>
          <div>
            <h2 className="mb-2 font-display text-lg text-ink">¿Viven otros perros en casa?</h2>
            <OpcionesSiNo
              etiqueta="¿Viven otros perros en casa?"
              valor={estado.tiene_otros_perros}
              onChange={(tiene_otros_perros) => setEstado((s) => ({ ...s, tiene_otros_perros }))}
            />
          </div>
          <div>
            <h2 className="mb-2 font-display text-lg text-ink">¿Viven otros gatos en casa?</h2>
            <OpcionesSiNo
              etiqueta="¿Viven otros gatos en casa?"
              valor={estado.tiene_otros_gatos}
              onChange={(tiene_otros_gatos) => setEstado((s) => ({ ...s, tiene_otros_gatos }))}
            />
          </div>
        </>
      )}

      {paso === 5 && (
        <>
          <GrupoOpciones
            titulo="¿Cuánta experiencia tienes con mascotas?"
            etiquetas={ETIQUETA_EXPERIENCIA}
            valor={estado.experiencia_previa}
            onChange={(experiencia_previa) => setEstado((s) => ({ ...s, experiencia_previa }))}
          />
          <CampoNumero
            id="hogar-presupuesto"
            etiqueta="Presupuesto mensual en pesos (opcional)"
            ayuda="Puedes dejarlo vacío. Si lo dices, lo usamos para no mostrarte mascotas cuyo cuidado se te haga cuesta arriba."
            valor={estado.presupuesto_mensual_cop}
            min={0}
            onChange={(valor) => setEstado((s) => ({ ...s, presupuesto_mensual_cop: valor }))}
          />
        </>
      )}

      {paso === 6 && (
        <>
          <GrupoMultiple
            titulo="¿Qué especies te interesan?"
            etiquetas={ETIQUETA_ESPECIE_ADOPCION}
            valores={estado.preferencia_especies}
            onChange={(preferencia_especies) => setEstado((s) => ({ ...s, preferencia_especies }))}
          />
          <GrupoMultiple
            titulo="¿Qué tamaños prefieres?"
            etiquetas={ETIQUETA_TAMANO_MASCOTA}
            valores={estado.preferencia_tamanos}
            onChange={(preferencia_tamanos) => setEstado((s) => ({ ...s, preferencia_tamanos }))}
          />
          <GrupoOpciones
            titulo="¿Qué nivel de energía prefieres?"
            etiquetas={ETIQUETA_ENERGIA}
            valor={estado.preferencia_energia}
            onChange={(preferencia_energia) => setEstado((s) => ({ ...s, preferencia_energia }))}
          />
        </>
      )}
    </div>
  );
}
