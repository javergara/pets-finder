import { type FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiError, publicarMascota } from '../api/client';
import { DEMO_SHELTER_ID } from '../lib/constants';

// Mismo patrón visual de chips de opción única que src/web/src/screens/Cuestionario.tsx
// (feature 08-onboarding-cuestionario), reutilizado aquí para mantener consistencia
// visual sin extraer un componente compartido (fuera de alcance de este paso).

const ESPECIE_OPCIONES = [
  { valor: 'perro', etiqueta: 'Perro' },
  { valor: 'gato', etiqueta: 'Gato' },
];

const SEXO_OPCIONES = [
  { valor: 'macho', etiqueta: 'Macho' },
  { valor: 'hembra', etiqueta: 'Hembra' },
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

interface EstadoFormulario {
  nombre: string;
  especie: string | null;
  raza: string;
  sexo: string | null;
  edad_meses: number;
  tamano: string | null;
  energia: string | null;
  historia: string;
  tagsTexto: string;
  esterilizado: boolean;
  vacunas_al_dia: boolean;
  microchip: boolean;
  desparasitado: boolean;
  apto_ninos: boolean;
  apto_perros: boolean;
  apto_gatos: boolean;
}

// Defaults consistentes con src/api/adopta_api/schemas/pet.py::PetIn: flags de
// salud conservadores (False) y flags de convivencia optimistas (True).
const ESTADO_INICIAL: EstadoFormulario = {
  nombre: '',
  especie: null,
  raza: '',
  sexo: null,
  edad_meses: 0,
  tamano: null,
  energia: null,
  historia: '',
  tagsTexto: '',
  esterilizado: false,
  vacunas_al_dia: false,
  microchip: false,
  desparasitado: false,
  apto_ninos: true,
  apto_perros: true,
  apto_gatos: true,
};

function formularioValido(estado: EstadoFormulario): boolean {
  return (
    estado.nombre.trim().length > 0 &&
    estado.raza.trim().length > 0 &&
    estado.historia.trim().length > 0 &&
    estado.especie !== null &&
    estado.sexo !== null &&
    estado.tamano !== null &&
    estado.energia !== null
  );
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
  valor: boolean;
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

export function PublicarMascota() {
  const [estado, setEstado] = useState<EstadoFormulario>(ESTADO_INICIAL);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!formularioValido(estado)) {
      setError(
        'Completa nombre, raza, historia y elige especie, sexo, tamaño y energía antes de publicar.',
      );
      return;
    }

    setError(null);
    setEnviando(true);
    try {
      await publicarMascota({
        shelter_id: DEMO_SHELTER_ID,
        nombre: estado.nombre.trim(),
        especie: estado.especie!,
        raza: estado.raza.trim(),
        sexo: estado.sexo!,
        edad_meses: estado.edad_meses,
        tamano: estado.tamano!,
        energia: estado.energia!,
        historia: estado.historia.trim(),
        tags: estado.tagsTexto
          .split(',')
          .map((tag) => tag.trim())
          .filter((tag) => tag.length > 0),
        esterilizado: estado.esterilizado,
        vacunas_al_dia: estado.vacunas_al_dia,
        microchip: estado.microchip,
        desparasitado: estado.desparasitado,
        apto_ninos: estado.apto_ninos,
        apto_perros: estado.apto_perros,
        apto_gatos: estado.apto_gatos,
      });
      navigate('/refugio');
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'No pudimos publicar la mascota. Intenta de nuevo.',
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="mx-auto mt-8 max-w-lg p-6">
      <h1 className="mb-2 font-display text-2xl text-ink">Publicar mascota</h1>
      <p className="mb-6 text-sm text-muted">
        Cuéntanos sobre la mascota que quieres poner en adopción. Sin fotos por ahora: puedes
        agregarlas más adelante.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <div>
          <label htmlFor="publicar-nombre" className="text-sm font-medium text-ink-soft">
            Nombre
          </label>
          <input
            id="publicar-nombre"
            type="text"
            value={estado.nombre}
            onChange={(e) => setEstado((s) => ({ ...s, nombre: e.target.value }))}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <h2 className="mb-3 font-display text-lg text-ink">Especie</h2>
          <div className="grid grid-cols-2 gap-3">
            {ESPECIE_OPCIONES.map((opcion) => (
              <OpcionCard
                key={opcion.valor}
                etiqueta={opcion.etiqueta}
                seleccionada={estado.especie === opcion.valor}
                onClick={() => setEstado((s) => ({ ...s, especie: opcion.valor }))}
              />
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="publicar-raza" className="text-sm font-medium text-ink-soft">
            Raza
          </label>
          <input
            id="publicar-raza"
            type="text"
            value={estado.raza}
            onChange={(e) => setEstado((s) => ({ ...s, raza: e.target.value }))}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <h2 className="mb-3 font-display text-lg text-ink">Sexo</h2>
          <div className="grid grid-cols-2 gap-3">
            {SEXO_OPCIONES.map((opcion) => (
              <OpcionCard
                key={opcion.valor}
                etiqueta={opcion.etiqueta}
                seleccionada={estado.sexo === opcion.valor}
                onClick={() => setEstado((s) => ({ ...s, sexo: opcion.valor }))}
              />
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="publicar-edad" className="text-sm font-medium text-ink-soft">
            Edad (meses)
          </label>
          <input
            id="publicar-edad"
            type="number"
            min={0}
            value={estado.edad_meses}
            onChange={(e) => setEstado((s) => ({ ...s, edad_meses: Number(e.target.value) }))}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-3 text-ink"
          />
        </div>

        <div>
          <h2 className="mb-3 font-display text-lg text-ink">Tamaño</h2>
          <div className="grid grid-cols-3 gap-3">
            {TAMANO_OPCIONES.map((opcion) => (
              <OpcionCard
                key={opcion.valor}
                etiqueta={opcion.etiqueta}
                seleccionada={estado.tamano === opcion.valor}
                onClick={() => setEstado((s) => ({ ...s, tamano: opcion.valor }))}
              />
            ))}
          </div>
        </div>

        <div>
          <h2 className="mb-3 font-display text-lg text-ink">Energía</h2>
          <div className="grid grid-cols-3 gap-3">
            {ENERGIA_OPCIONES.map((opcion) => (
              <OpcionCard
                key={opcion.valor}
                etiqueta={opcion.etiqueta}
                seleccionada={estado.energia === opcion.valor}
                onClick={() => setEstado((s) => ({ ...s, energia: opcion.valor }))}
              />
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="publicar-historia" className="text-sm font-medium text-ink-soft">
            Historia
          </label>
          <textarea
            id="publicar-historia"
            value={estado.historia}
            onChange={(e) => setEstado((s) => ({ ...s, historia: e.target.value }))}
            rows={4}
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <label htmlFor="publicar-tags" className="text-sm font-medium text-ink-soft">
            Tags (separados por coma, opcional)
          </label>
          <input
            id="publicar-tags"
            type="text"
            value={estado.tagsTexto}
            onChange={(e) => setEstado((s) => ({ ...s, tagsTexto: e.target.value }))}
            placeholder="juguetón, tranquilo, bueno con niños"
            className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
          />
        </div>

        <div>
          <h2 className="mb-3 font-display text-lg text-ink">Salud</h2>
          <div className="flex flex-col gap-4">
            <div>
              <p className="mb-2 text-sm text-ink-soft">¿Está esterilizado/a?</p>
              <OpcionesSiNo
                valor={estado.esterilizado}
                onChange={(valor) => setEstado((s) => ({ ...s, esterilizado: valor }))}
              />
            </div>
            <div>
              <p className="mb-2 text-sm text-ink-soft">¿Tiene vacunas al día?</p>
              <OpcionesSiNo
                valor={estado.vacunas_al_dia}
                onChange={(valor) => setEstado((s) => ({ ...s, vacunas_al_dia: valor }))}
              />
            </div>
            <div>
              <p className="mb-2 text-sm text-ink-soft">¿Tiene microchip?</p>
              <OpcionesSiNo
                valor={estado.microchip}
                onChange={(valor) => setEstado((s) => ({ ...s, microchip: valor }))}
              />
            </div>
            <div>
              <p className="mb-2 text-sm text-ink-soft">¿Está desparasitado/a?</p>
              <OpcionesSiNo
                valor={estado.desparasitado}
                onChange={(valor) => setEstado((s) => ({ ...s, desparasitado: valor }))}
              />
            </div>
          </div>
        </div>

        <div>
          <h2 className="mb-3 font-display text-lg text-ink">Convivencia</h2>
          <div className="flex flex-col gap-4">
            <div>
              <p className="mb-2 text-sm text-ink-soft">¿Es apta para convivir con niños?</p>
              <OpcionesSiNo
                valor={estado.apto_ninos}
                onChange={(valor) => setEstado((s) => ({ ...s, apto_ninos: valor }))}
              />
            </div>
            <div>
              <p className="mb-2 text-sm text-ink-soft">¿Es apta para convivir con otros perros?</p>
              <OpcionesSiNo
                valor={estado.apto_perros}
                onChange={(valor) => setEstado((s) => ({ ...s, apto_perros: valor }))}
              />
            </div>
            <div>
              <p className="mb-2 text-sm text-ink-soft">¿Es apta para convivir con gatos?</p>
              <OpcionesSiNo
                valor={estado.apto_gatos}
                onChange={(valor) => setEstado((s) => ({ ...s, apto_gatos: valor }))}
              />
            </div>
          </div>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button
          type="submit"
          disabled={enviando}
          className="rounded-full bg-forest px-4 py-3 font-medium text-bg disabled:opacity-60"
        >
          {enviando ? 'Publicando…' : 'Publicar mascota'}
        </button>
      </form>
    </div>
  );
}
