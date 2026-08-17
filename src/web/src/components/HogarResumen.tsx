import type { PerfilHogar } from '../api/types';
import { ETIQUETA_ESPACIO, ETIQUETA_EXPERIENCIA, ETIQUETA_VIVIENDA } from '../lib/hogar';

// El cuestionario de hogar de quien adopta, leído por quien publicó la mascota
// (AD-05). Es el contenido principal del detalle: sin esto, decidir a quién se
// le entrega un animal sería decidir por un nombre y una foto.
//
// Los tres catálogos de copy se **importan** de `lib/hogar.ts`, que es donde los
// escribe el wizard que llena estos datos: en `adopta-v1` este componente
// declaraba sus propios `Record<string, string>` y la misma respuesta podía
// leerse con dos palabras distintas según la pantalla. Al importarlos, además,
// son `Record<Literal, string>`: un valor nuevo en el catálogo no compila sin
// decidir cómo se lee aquí.
//
// ⚠️ **No se pintan el presupuesto ni las preferencias de búsqueda**, y no es un
// olvido. El presupuesto es un dato económico personal que ya viaja condensado
// en el score de afinidad (`services/afinidad.py` lo usa para el costo de
// mantenimiento), así que enseñárselo con nombre y apellido a quien publica
// sería repartir información sensible que nadie necesita leer para decidir. Las
// preferencias (especie, tamaño, energía) describen lo que esa persona busca en
// general, no si este hogar le queda bien a ESTA mascota.

/** Un sí/no del hogar, en el idioma del cuestionario. */
function siNo(valor: boolean): string {
  return valor ? 'Sí' : 'No';
}

export function HogarResumen({ home }: { home: PerfilHogar }) {
  const filas: Array<[string, string]> = [
    ['Vivienda', ETIQUETA_VIVIENDA[home.vivienda]],
    ['Espacio exterior', ETIQUETA_ESPACIO[home.espacio_exterior]],
    ['Personas en casa', String(home.personas_en_casa)],
    ['Niños en casa', siNo(home.tiene_ninos)],
    ['Otros perros', siNo(home.tiene_otros_perros)],
    ['Otros gatos', siNo(home.tiene_otros_gatos)],
    ['Horas fuera al día', `${home.horas_fuera_dia} h`],
    ['Experiencia con mascotas', ETIQUETA_EXPERIENCIA[home.experiencia_previa]],
  ];

  return (
    <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
      {filas.map(([etiqueta, valor]) => (
        <div key={etiqueta}>
          <dt className="font-mono text-xs tracking-wide text-muted uppercase">{etiqueta}</dt>
          <dd className="text-ink-soft">{valor}</dd>
        </div>
      ))}
    </dl>
  );
}
