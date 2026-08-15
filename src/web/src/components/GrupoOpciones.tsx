import { OpcionCard } from './OpcionCard';

// Un catálogo cerrado (especie, sexo, tamaño, energía) como chips de opción
// única (AD-02).
//
// Vivía dentro de `screens/PublicarMascota.tsx`, que llegó a 441 líneas en el
// paso 7 —por encima del tope de 400 que nos fijamos— y en el paso 8 crece con
// el puente desde un reporte. Sale aquí, junto a `OpcionCard`, porque es su
// envoltorio natural y porque el cuestionario de hogar (AD-04) elige por
// catálogos cerrados exactamente igual.
//
// El `role="group"` con el nombre del catálogo no es decoración: sin él "Perro"
// y "Mediana" flotan sueltos entre los treinta botones del formulario, tanto
// para un lector de pantalla como para los tests, que es como los distinguen.

type Props<T extends string> = {
  titulo: string;
  etiquetas: Record<T, string>;
  valor: T | null;
  onChange: (valor: T) => void;
};

export function GrupoOpciones<T extends string>({ titulo, etiquetas, valor, onChange }: Props<T>) {
  return (
    <div>
      <h2 className="mb-2 font-display text-lg text-ink">{titulo}</h2>
      <div role="group" aria-label={titulo} className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {(Object.entries(etiquetas) as [T, string][]).map(([opcion, etiqueta]) => (
          <OpcionCard
            key={opcion}
            etiqueta={etiqueta}
            seleccionada={valor === opcion}
            onClick={() => onChange(opcion)}
          />
        ))}
      </div>
    </div>
  );
}
