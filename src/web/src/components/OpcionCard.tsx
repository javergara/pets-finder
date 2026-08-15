// Chips de opción única (AD-02).
//
// En la era Adopta estos dos componentes estaban DUPLICADOS byte a byte entre
// `screens/Cuestionario.tsx` y `screens/PublicarMascota.tsx`, con un comentario
// que lo admitía ("sin extraer un componente compartido, fuera de alcance de este
// paso"). Se extraen aquí porque el cuestionario de hogar (AD-04) los vuelve a
// necesitar y la tercera copia era el momento de parar. `CampoNumero`, que vivía
// al lado, NO se extrae: tiene un solo uso.
//
// Paleta `forest`: el rojo de emergencia está reservado al dominio de perdidos y
// no entra en el módulo de adopción.

type OpcionCardProps = {
  etiqueta: string;
  seleccionada: boolean;
  onClick: () => void;
};

export function OpcionCard({ etiqueta, seleccionada, onClick }: OpcionCardProps) {
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

type OpcionesSiNoProps = {
  // `null` = todavía sin responder. Lo necesita el wizard de hogar (AD-04), que
  // no puede avanzar de paso hasta que la persona conteste; el formulario de
  // publicar arranca con un default explícito y nunca lo usa.
  valor: boolean | null;
  onChange: (valor: boolean) => void;
  // Nombre accesible del par. Sin él, un formulario con siete preguntas expone
  // catorce botones llamados "Sí"/"No" que ni un lector de pantalla ni un test
  // pueden distinguir; con él, cada par es un grupo con el texto de su pregunta.
  etiqueta?: string;
};

export function OpcionesSiNo({ valor, onChange, etiqueta }: OpcionesSiNoProps) {
  return (
    <div role="group" aria-label={etiqueta} className="grid grid-cols-2 gap-3">
      <OpcionCard etiqueta="Sí" seleccionada={valor === true} onClick={() => onChange(true)} />
      <OpcionCard etiqueta="No" seleccionada={valor === false} onClick={() => onChange(false)} />
    </div>
  );
}
