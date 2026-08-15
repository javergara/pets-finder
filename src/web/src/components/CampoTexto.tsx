// Un campo de texto con su etiqueta (AD-02).
//
// El bloque `<div><label htmlFor><input id></div>` estaba escrito cinco veces en
// `screens/PublicarMascota.tsx`, con las mismas clases y trece líneas cada vez:
// era el último gordo del formulario después de sacar `GrupoOpciones` y
// `SeccionesSiNo`, y la pantalla no bajaba de 400 líneas sin él.
//
// El `id` es obligatorio y no se genera solo: es lo que une la etiqueta con el
// campo (y lo que hace que `getByLabelText` —o un lector de pantalla— los
// encuentre). Los campos con reglas propias (la edad, con `min`/`max`) siguen
// escritos a mano en su pantalla: este componente cubre el caso repetido, no
// todos los casos.

const CLASE_INPUT = 'mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink';

type Props = {
  id: string;
  etiqueta: string;
  valor: string;
  onChange: (valor: string) => void;
  tipo?: 'text' | 'tel';
  placeholder?: string;
  // Nota bajo el campo, para lo que no cabe en la etiqueta.
  ayuda?: string;
};

export function CampoTexto({
  id,
  etiqueta,
  valor,
  onChange,
  tipo = 'text',
  placeholder,
  ayuda,
}: Props) {
  return (
    <div>
      <label htmlFor={id} className="text-sm font-medium text-ink-soft">
        {etiqueta}
      </label>
      <input
        id={id}
        type={tipo}
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={CLASE_INPUT}
      />
      {ayuda && <p className="mt-1 text-xs text-muted">{ayuda}</p>}
    </div>
  );
}
