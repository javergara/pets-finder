import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiError, guardarHomeProfile, obtenerPerfil } from '../api/client';
import type { HomeProfile } from '../api/types';
import { getActiveUserId } from '../lib/session';

const TOTAL_PASOS = 6;

interface EstadoWizard {
  vivienda: string | null;
  espacio_exterior: string | null;
  personas_en_casa: number;
  tiene_ninos: boolean | null;
  tiene_otros_perros: boolean | null;
  tiene_otros_gatos: boolean | null;
  horas_fuera_dia: number;
  experiencia_previa: string | null;
  presupuesto_mensual_cop: number;
  preferencia_especies: string[];
  preferencia_tamanos: string[];
  preferencia_energia: string | null;
}

const ESTADO_INICIAL: EstadoWizard = {
  vivienda: null,
  espacio_exterior: null,
  personas_en_casa: 1,
  tiene_ninos: null,
  tiene_otros_perros: null,
  tiene_otros_gatos: null,
  horas_fuera_dia: 8,
  experiencia_previa: null,
  presupuesto_mensual_cop: 300000,
  preferencia_especies: [],
  preferencia_tamanos: [],
  preferencia_energia: null,
};

const VIVIENDA_OPCIONES = [
  { valor: 'apartamento', etiqueta: 'Apartamento' },
  { valor: 'casa', etiqueta: 'Casa' },
];

const ESPACIO_EXTERIOR_OPCIONES = [
  { valor: 'ninguno', etiqueta: 'Sin espacio exterior' },
  { valor: 'patio', etiqueta: 'Patio' },
  { valor: 'jardin', etiqueta: 'Jardín' },
];

const EXPERIENCIA_OPCIONES = [
  { valor: 'ninguna', etiqueta: 'Ninguna' },
  { valor: 'algo', etiqueta: 'Algo de experiencia' },
  { valor: 'mucha', etiqueta: 'Mucha experiencia' },
];

const ESPECIE_OPCIONES = [
  { valor: 'perro', etiqueta: 'Perro' },
  { valor: 'gato', etiqueta: 'Gato' },
];

const TAMANO_OPCIONES = [
  { valor: 'pequeño', etiqueta: 'Pequeño' },
  { valor: 'mediano', etiqueta: 'Mediano' },
  { valor: 'grande', etiqueta: 'Grande' },
];

const ENERGIA_OPCIONES = [
  { valor: 'baja', etiqueta: 'Baja' },
  { valor: 'media', etiqueta: 'Media' },
  { valor: 'alta', etiqueta: 'Alta' },
];

function alternarValor(lista: string[], valor: string): string[] {
  return lista.includes(valor) ? lista.filter((v) => v !== valor) : [...lista, valor];
}

function pasoValido(paso: number, estado: EstadoWizard): boolean {
  switch (paso) {
    case 1:
      return estado.vivienda !== null && estado.espacio_exterior !== null;
    case 2:
      return estado.tiene_ninos !== null;
    case 3:
      return estado.horas_fuera_dia >= 0;
    case 4:
      return estado.tiene_otros_perros !== null && estado.tiene_otros_gatos !== null;
    case 5:
      return estado.experiencia_previa !== null && estado.presupuesto_mensual_cop >= 0;
    case 6:
      return (
        estado.preferencia_especies.length > 0 &&
        estado.preferencia_tamanos.length > 0 &&
        estado.preferencia_energia !== null
      );
    default:
      return false;
  }
}

interface OpcionCardProps {
  etiqueta: string;
  seleccionada: boolean;
  onClick: () => void;
}

function OpcionCard({ etiqueta, seleccionada, onClick }: OpcionCardProps) {
  return (
    <button
      type="button"
      aria-pressed={seleccionada}
      onClick={onClick}
      className={`min-h-[56px] rounded-2xl border px-4 py-3 text-left font-medium transition ${
        seleccionada
          ? 'border-forest bg-forest-tint text-ink'
          : 'border-line bg-surface text-ink-soft hover:border-forest-tint-line'
      }`}
    >
      {etiqueta}
    </button>
  );
}

interface OpcionesSiNoProps {
  valor: boolean | null;
  onChange: (valor: boolean) => void;
}

function OpcionesSiNo({ valor, onChange }: OpcionesSiNoProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      <OpcionCard etiqueta="Sí" seleccionada={valor === true} onClick={() => onChange(true)} />
      <OpcionCard etiqueta="No" seleccionada={valor === false} onClick={() => onChange(false)} />
    </div>
  );
}

interface CampoNumeroProps {
  id: string;
  etiqueta: string;
  valor: number;
  onChange: (valor: number) => void;
  min?: number;
  max?: number;
}

function CampoNumero({ id, etiqueta, valor, onChange, min = 0, max }: CampoNumeroProps) {
  return (
    <div>
      <label htmlFor={id} className="text-sm font-medium text-ink-soft">
        {etiqueta}
      </label>
      <input
        id={id}
        type="number"
        min={min}
        max={max}
        value={valor}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-3 text-ink"
      />
    </div>
  );
}

interface PasoProps {
  estado: EstadoWizard;
  setEstado: React.Dispatch<React.SetStateAction<EstadoWizard>>;
}

function Paso1({ estado, setEstado }: PasoProps) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="mb-3 font-display text-lg text-ink">¿Dónde vives?</h2>
        <div className="grid grid-cols-2 gap-3">
          {VIVIENDA_OPCIONES.map((opcion) => (
            <OpcionCard
              key={opcion.valor}
              etiqueta={opcion.etiqueta}
              seleccionada={estado.vivienda === opcion.valor}
              onClick={() => setEstado((s) => ({ ...s, vivienda: opcion.valor }))}
            />
          ))}
        </div>
      </div>
      <div>
        <h2 className="mb-3 font-display text-lg text-ink">¿Tienes espacio exterior?</h2>
        <div className="grid grid-cols-3 gap-3">
          {ESPACIO_EXTERIOR_OPCIONES.map((opcion) => (
            <OpcionCard
              key={opcion.valor}
              etiqueta={opcion.etiqueta}
              seleccionada={estado.espacio_exterior === opcion.valor}
              onClick={() => setEstado((s) => ({ ...s, espacio_exterior: opcion.valor }))}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function Paso2({ estado, setEstado }: PasoProps) {
  return (
    <div className="flex flex-col gap-6">
      <CampoNumero
        id="cuestionario-personas"
        etiqueta="¿Cuántas personas viven en tu hogar?"
        valor={estado.personas_en_casa}
        min={1}
        onChange={(valor) => setEstado((s) => ({ ...s, personas_en_casa: valor }))}
      />
      <div>
        <h2 className="mb-3 font-display text-lg text-ink">¿Hay niños en casa?</h2>
        <OpcionesSiNo
          valor={estado.tiene_ninos}
          onChange={(valor) => setEstado((s) => ({ ...s, tiene_ninos: valor }))}
        />
      </div>
    </div>
  );
}

function Paso3({ estado, setEstado }: PasoProps) {
  return (
    <div className="flex flex-col gap-6">
      <CampoNumero
        id="cuestionario-horas"
        etiqueta="¿Cuántas horas pasas fuera de casa al día?"
        valor={estado.horas_fuera_dia}
        min={0}
        max={24}
        onChange={(valor) => setEstado((s) => ({ ...s, horas_fuera_dia: valor }))}
      />
    </div>
  );
}

function Paso4({ estado, setEstado }: PasoProps) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="mb-3 font-display text-lg text-ink">¿Tienes otros perros en casa?</h2>
        <OpcionesSiNo
          valor={estado.tiene_otros_perros}
          onChange={(valor) => setEstado((s) => ({ ...s, tiene_otros_perros: valor }))}
        />
      </div>
      <div>
        <h2 className="mb-3 font-display text-lg text-ink">¿Tienes otros gatos en casa?</h2>
        <OpcionesSiNo
          valor={estado.tiene_otros_gatos}
          onChange={(valor) => setEstado((s) => ({ ...s, tiene_otros_gatos: valor }))}
        />
      </div>
    </div>
  );
}

function Paso5({ estado, setEstado }: PasoProps) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="mb-3 font-display text-lg text-ink">
          ¿Cuánta experiencia previa tienes con mascotas?
        </h2>
        <div className="grid grid-cols-3 gap-3">
          {EXPERIENCIA_OPCIONES.map((opcion) => (
            <OpcionCard
              key={opcion.valor}
              etiqueta={opcion.etiqueta}
              seleccionada={estado.experiencia_previa === opcion.valor}
              onClick={() => setEstado((s) => ({ ...s, experiencia_previa: opcion.valor }))}
            />
          ))}
        </div>
      </div>
      <CampoNumero
        id="cuestionario-presupuesto"
        etiqueta="¿Cuál es tu presupuesto mensual estimado para tu mascota (COP)?"
        valor={estado.presupuesto_mensual_cop}
        min={0}
        onChange={(valor) => setEstado((s) => ({ ...s, presupuesto_mensual_cop: valor }))}
      />
    </div>
  );
}

function Paso6({ estado, setEstado }: PasoProps) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="mb-3 font-display text-lg text-ink">¿Qué especie o especies prefieres?</h2>
        <div className="grid grid-cols-2 gap-3">
          {ESPECIE_OPCIONES.map((opcion) => (
            <OpcionCard
              key={opcion.valor}
              etiqueta={opcion.etiqueta}
              seleccionada={estado.preferencia_especies.includes(opcion.valor)}
              onClick={() =>
                setEstado((s) => ({
                  ...s,
                  preferencia_especies: alternarValor(s.preferencia_especies, opcion.valor),
                }))
              }
            />
          ))}
        </div>
      </div>
      <div>
        <h2 className="mb-3 font-display text-lg text-ink">¿Qué tamaño o tamaños prefieres?</h2>
        <div className="grid grid-cols-3 gap-3">
          {TAMANO_OPCIONES.map((opcion) => (
            <OpcionCard
              key={opcion.valor}
              etiqueta={opcion.etiqueta}
              seleccionada={estado.preferencia_tamanos.includes(opcion.valor)}
              onClick={() =>
                setEstado((s) => ({
                  ...s,
                  preferencia_tamanos: alternarValor(s.preferencia_tamanos, opcion.valor),
                }))
              }
            />
          ))}
        </div>
      </div>
      <div>
        <h2 className="mb-3 font-display text-lg text-ink">¿Qué nivel de energía prefieres?</h2>
        <div className="grid grid-cols-3 gap-3">
          {ENERGIA_OPCIONES.map((opcion) => (
            <OpcionCard
              key={opcion.valor}
              etiqueta={opcion.etiqueta}
              seleccionada={estado.preferencia_energia === opcion.valor}
              onClick={() => setEstado((s) => ({ ...s, preferencia_energia: opcion.valor }))}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

const PASOS = [Paso1, Paso2, Paso3, Paso4, Paso5, Paso6];

export function Cuestionario() {
  const [paso, setPaso] = useState(1);
  const [estado, setEstado] = useState<EstadoWizard>(ESTADO_INICIAL);
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    obtenerPerfil(getActiveUserId()).then((perfil) => {
      const home = perfil.home_profile;
      if (home) {
        setEstado({
          vivienda: home.vivienda,
          espacio_exterior: home.espacio_exterior,
          personas_en_casa: home.personas_en_casa,
          tiene_ninos: home.tiene_ninos,
          tiene_otros_perros: home.tiene_otros_perros,
          tiene_otros_gatos: home.tiene_otros_gatos,
          horas_fuera_dia: home.horas_fuera_dia,
          experiencia_previa: home.experiencia_previa,
          presupuesto_mensual_cop: home.presupuesto_mensual_cop,
          preferencia_especies: home.preferencia_especies,
          preferencia_tamanos: home.preferencia_tamanos,
          preferencia_energia: home.preferencia_energia,
        });
      }
    });
  }, []);

  async function handleSubmit() {
    if (!pasoValido(TOTAL_PASOS, estado)) return;
    setError(null);
    setGuardando(true);
    try {
      const payload: HomeProfile = {
        vivienda: estado.vivienda!,
        espacio_exterior: estado.espacio_exterior!,
        personas_en_casa: estado.personas_en_casa,
        tiene_ninos: estado.tiene_ninos!,
        tiene_otros_perros: estado.tiene_otros_perros!,
        tiene_otros_gatos: estado.tiene_otros_gatos!,
        horas_fuera_dia: estado.horas_fuera_dia,
        experiencia_previa: estado.experiencia_previa!,
        presupuesto_mensual_cop: estado.presupuesto_mensual_cop,
        preferencia_especies: estado.preferencia_especies,
        preferencia_tamanos: estado.preferencia_tamanos,
        preferencia_energia: estado.preferencia_energia!,
      };
      await guardarHomeProfile(getActiveUserId(), payload);
      navigate('/descubrir');
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'No pudimos guardar tu cuestionario. Intenta de nuevo.',
      );
    } finally {
      setGuardando(false);
    }
  }

  function handleContinuar() {
    if (paso < TOTAL_PASOS) {
      setPaso((p) => p + 1);
    } else {
      void handleSubmit();
    }
  }

  const PasoActual = PASOS[paso - 1];

  return (
    <div className="mx-auto mt-8 max-w-lg p-6">
      <div className="mb-6">
        <div className="h-2 w-full overflow-hidden rounded-full bg-surface-alt">
          <div
            className="h-full rounded-full bg-forest transition-all"
            style={{ width: `${(paso / TOTAL_PASOS) * 100}%` }}
          />
        </div>
        <p className="mt-2 font-mono text-xs tracking-wide text-muted-2 uppercase">
          Paso {paso} de {TOTAL_PASOS}
        </p>
      </div>

      <div className="mb-6 rounded-2xl bg-surface-alt p-4 text-sm text-ink-soft">
        Responde con honestidad: esta información nos ayuda a mostrarte mascotas realmente
        compatibles con tu hogar y evita devoluciones que le hacen daño al animal.
      </div>

      <PasoActual estado={estado} setEstado={setEstado} />

      {error && <p className="mt-6 text-sm text-danger">{error}</p>}

      <div className="mt-8 flex items-center justify-between gap-3">
        {paso > 1 ? (
          <button
            type="button"
            onClick={() => setPaso((p) => p - 1)}
            className="rounded-full border border-line px-4 py-3 font-medium text-ink-soft"
          >
            Atrás
          </button>
        ) : (
          <span />
        )}
        <button
          type="button"
          onClick={handleContinuar}
          disabled={!pasoValido(paso, estado) || guardando}
          className="rounded-full bg-forest px-6 py-3 font-medium text-bg disabled:opacity-60"
        >
          {paso === TOTAL_PASOS ? (guardando ? 'Guardando…' : 'Terminar') : 'Continuar'}
        </button>
      </div>
    </div>
  );
}
