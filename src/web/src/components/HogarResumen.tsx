import type { HomeProfile } from '../api/types';

const VIVIENDA_LABEL: Record<string, string> = {
  apartamento: 'Apartamento',
  casa: 'Casa',
};

const ESPACIO_EXTERIOR_LABEL: Record<string, string> = {
  ninguno: 'Sin espacio exterior',
  patio: 'Patio',
  jardin: 'Jardín',
};

export function HogarResumen({ home }: { home: HomeProfile }) {
  const filas: Array<[string, string]> = [
    ['Vivienda', VIVIENDA_LABEL[home.vivienda] ?? home.vivienda],
    ['Espacio exterior', ESPACIO_EXTERIOR_LABEL[home.espacio_exterior] ?? home.espacio_exterior],
    ['Personas en casa', String(home.personas_en_casa)],
    ['Niños en casa', home.tiene_ninos ? 'Sí' : 'No'],
    ['Otros perros', home.tiene_otros_perros ? 'Sí' : 'No'],
    ['Otros gatos', home.tiene_otros_gatos ? 'Sí' : 'No'],
    ['Horas fuera al día', `${home.horas_fuera_dia}h`],
  ];

  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
      {filas.map(([etiqueta, valor]) => (
        <div key={etiqueta}>
          <dt className="font-mono text-xs tracking-wide text-muted-2 uppercase">{etiqueta}</dt>
          <dd className="text-ink-soft">{valor}</dd>
        </div>
      ))}
    </dl>
  );
}
