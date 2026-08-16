import type {
  EnergiaMascota,
  EspacioExterior,
  EspecieAdopcion,
  ExperienciaPrevia,
  TamanoMascota,
  ViviendaHogar,
} from '../api/types';

// El cuestionario de hogar como dato puro (AD-04): catálogos de copy, forma del
// estado y qué significa "este paso está contestado".
//
// Vive aquí y no junto al JSX por la misma razón que `lib/adopcion.ts`: no
// depende de React, se prueba sin montar nada, y dejarlo en el archivo de
// componentes hacía saltar el aviso de fast-refresh de oxlint.
//
// ⚠️ Los tres catálogos propios del hogar (vivienda, espacio, experiencia) tienen
// que coincidir con los `Literal` de `schemas/user.py`, que a su vez son las
// llaves de los diccionarios de `services/afinidad.py`: un valor que no esté en
// catálogo no da un score raro, hace saltar un `KeyError` en el deck.

export const TOTAL_PASOS = 6;

export const ETIQUETA_VIVIENDA: Record<ViviendaHogar, string> = {
  apartamento: 'Apartamento',
  casa: 'Casa',
};

export const ETIQUETA_ESPACIO: Record<EspacioExterior, string> = {
  ninguno: 'Sin espacio exterior',
  patio: 'Patio',
  jardin: 'Jardín',
};

export const ETIQUETA_EXPERIENCIA: Record<ExperienciaPrevia, string> = {
  ninguna: 'Ninguna',
  algo: 'Algo de experiencia',
  mucha: 'Mucha experiencia',
};

export type EstadoWizard = {
  vivienda: ViviendaHogar | null;
  espacio_exterior: EspacioExterior | null;
  personas_en_casa: number;
  tiene_ninos: boolean | null;
  tiene_otros_perros: boolean | null;
  tiene_otros_gatos: boolean | null;
  horas_fuera_dia: number;
  experiencia_previa: ExperienciaPrevia | null;
  // `null` = "prefiero no decirlo", que es un valor válido y no un hueco.
  presupuesto_mensual_cop: number | null;
  preferencia_especies: EspecieAdopcion[];
  preferencia_tamanos: TamanoMascota[];
  preferencia_energia: EnergiaMascota | null;
};

export const ESTADO_INICIAL: EstadoWizard = {
  vivienda: null,
  espacio_exterior: null,
  personas_en_casa: 1,
  tiene_ninos: null,
  tiene_otros_perros: null,
  tiene_otros_gatos: null,
  horas_fuera_dia: 8,
  experiencia_previa: null,
  presupuesto_mensual_cop: null,
  preferencia_especies: [],
  preferencia_tamanos: [],
  preferencia_energia: null,
};

export function alternar<T>(lista: T[], valor: T): T[] {
  return lista.includes(valor) ? lista.filter((v) => v !== valor) : [...lista, valor];
}

/** Qué falta por contestar en cada paso. El botón lee esto, no al revés. */
export function pasoValido(paso: number, estado: EstadoWizard): boolean {
  switch (paso) {
    case 1:
      return estado.vivienda !== null && estado.espacio_exterior !== null;
    case 2:
      return estado.personas_en_casa >= 1 && estado.tiene_ninos !== null;
    case 3:
      return estado.horas_fuera_dia >= 0 && estado.horas_fuera_dia <= 24;
    case 4:
      return estado.tiene_otros_perros !== null && estado.tiene_otros_gatos !== null;
    case 5:
      // El presupuesto no entra en la validación: es opcional. Solo se exige que
      // no sea negativo si alguien escribió algo.
      return (
        estado.experiencia_previa !== null &&
        (estado.presupuesto_mensual_cop === null || estado.presupuesto_mensual_cop >= 0)
      );
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
