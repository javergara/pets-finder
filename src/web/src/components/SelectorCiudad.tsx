import { NOMBRES_ZONAS, ZONA_OTRO } from '../lib/ciudades';

type Props = {
  id?: string;
  value: string;
  onChange: (zona: string) => void;
  // "Otro lugar de Colombia" al reportar; la vista "Todo Colombia" del mapa la
  // añade quien lo use (MapaReportes) porque no es una zona de reporte.
  incluirOtro?: boolean;
  // Con placeholder el selector arranca sin zona elegida (value ""): nadie
  // reporta en Armenia "por defecto" solo por no tocar el select.
  placeholder?: string;
};

export function SelectorCiudad({
  id = 'selector-zona',
  value,
  onChange,
  incluirOtro,
  placeholder,
}: Props) {
  return (
    <select
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded-xl border border-line bg-surface px-3 py-2 text-ink"
    >
      {placeholder && <option value="">{placeholder}</option>}
      {NOMBRES_ZONAS.map((zona) => (
        <option key={zona} value={zona}>
          {zona}
        </option>
      ))}
      {incluirOtro && <option value={ZONA_OTRO}>Otro lugar de Colombia</option>}
    </select>
  );
}
