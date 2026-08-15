import type { FlagsMascota } from '../lib/adopcion';
import { OpcionesSiNo } from './OpcionCard';

// Salud y convivencia: los siete sí/no de una mascota en adopción (AD-02).
//
// Segunda mitad del adelgazamiento de `screens/PublicarMascota.tsx` (441 líneas
// tras el paso 7, tope 400): con `GrupoOpciones` fuera seguía sin caber. Las dos
// secciones son un bloque cerrado —copy + JSX— que el formulario solo consume.
// Los valores iniciales de las respuestas viven en `lib/adopcion.ts`, que es
// donde va el dato del dominio.
//
// Los dos grupos se pintan con el mismo bloque: son idénticos salvo el título y
// las preguntas, y escribirlos dos veces en el JSX era la mitad del formulario.

const SECCIONES: {
  titulo: string;
  preguntas: { campo: keyof FlagsMascota; pregunta: string }[];
}[] = [
  {
    titulo: 'Salud',
    preguntas: [
      { campo: 'esterilizado', pregunta: '¿Está esterilizada?' },
      { campo: 'vacunas_al_dia', pregunta: '¿Tiene las vacunas al día?' },
      { campo: 'microchip', pregunta: '¿Tiene microchip?' },
      { campo: 'desparasitado', pregunta: '¿Está desparasitada?' },
    ],
  },
  {
    titulo: 'Convivencia',
    preguntas: [
      { campo: 'apto_ninos', pregunta: '¿Convive bien con niños?' },
      { campo: 'apto_perros', pregunta: '¿Convive bien con otros perros?' },
      { campo: 'apto_gatos', pregunta: '¿Convive bien con gatos?' },
    ],
  },
];

type Props = {
  flags: FlagsMascota;
  onChange: (campo: keyof FlagsMascota, valor: boolean) => void;
};

export function SeccionesSiNo({ flags, onChange }: Props) {
  return (
    <>
      {SECCIONES.map(({ titulo, preguntas }) => (
        <div key={titulo}>
          <h2 className="mb-2 font-display text-lg text-ink">{titulo}</h2>
          <div className="flex flex-col gap-4">
            {preguntas.map(({ campo, pregunta }) => (
              <div key={campo}>
                <p className="mb-2 text-sm text-ink-soft">{pregunta}</p>
                <OpcionesSiNo
                  etiqueta={pregunta}
                  valor={flags[campo]}
                  onChange={(valor) => onChange(campo, valor)}
                />
              </div>
            ))}
          </div>
        </div>
      ))}
    </>
  );
}
