import { describe, expect, it } from 'vitest';
import type { AccionSolicitud, EstadoSolicitud, Mascota } from '../api/types';
import {
  categoriaEdad,
  contarFiltrosActivos,
  edadLegible,
  ETIQUETA_ACCION_SOLICITUD,
  ETIQUETA_ESTADO_SOLICITUD,
  FILTROS_ADOPCION_DEFAULT,
  tituloMascota,
} from './adopcion';

function mascota(
  overrides: Partial<Mascota> = {},
): Pick<Mascota, 'nombre' | 'especie' | 'tamano' | 'raza'> {
  return {
    nombre: 'Nala',
    especie: 'perro' as const,
    tamano: 'mediano' as const,
    raza: null,
    ...overrides,
  };
}

describe('edadLegible', () => {
  it('bajo el año habla en meses, en singular cuando toca', () => {
    expect(edadLegible(1)).toBe('1 mes');
    expect(edadLegible(3)).toBe('3 meses');
    expect(edadLegible(11)).toBe('11 meses');
  });

  // El bug portado de adopta-v1: `Math.round(edad_meses / 12)` mostraba
  // "0 años" para un cachorro de 5 meses (y "2 años" para uno de 18).
  it('un cachorro de 5 meses dice "5 meses", nunca "0 años"', () => {
    expect(edadLegible(5)).toBe('5 meses');
    expect(edadLegible(5)).not.toContain('año');
  });

  it('desde el año habla en años, en singular cuando toca', () => {
    expect(edadLegible(12)).toBe('1 año');
    expect(edadLegible(36)).toBe('3 años');
    expect(edadLegible(96)).toBe('8 años');
  });

  // Decisión documentada en adopcion.ts: los años se truncan, no se redondean.
  it('trunca los meses sueltos en vez de redondear hacia arriba', () => {
    expect(edadLegible(18)).toBe('1 año');
    expect(edadLegible(23)).toBe('1 año');
    expect(edadLegible(24)).toBe('2 años');
  });

  it('no dice "0 meses" para una recién nacida', () => {
    expect(edadLegible(0)).toBe('Menos de 1 mes');
  });
});

describe('categoriaEdad', () => {
  it('clasifica los cuatro tramos', () => {
    expect(categoriaEdad(4)).toBe('cachorro');
    expect(categoriaEdad(20)).toBe('joven');
    expect(categoriaEdad(60)).toBe('adulto');
    expect(categoriaEdad(120)).toBe('senior');
  });

  it('respeta los bordes exactos de cada tramo', () => {
    expect(categoriaEdad(0)).toBe('cachorro');
    expect(categoriaEdad(11)).toBe('cachorro');
    expect(categoriaEdad(12)).toBe('joven');
    expect(categoriaEdad(35)).toBe('joven');
    expect(categoriaEdad(36)).toBe('adulto');
    expect(categoriaEdad(83)).toBe('adulto');
    expect(categoriaEdad(84)).toBe('senior');
  });
});

describe('tituloMascota', () => {
  it('el nombre manda cuando lo tiene', () => {
    expect(tituloMascota(mascota({ nombre: 'Nala', raza: 'Labrador' }))).toBe('Nala');
  });

  it('sin nombre compone especie + tamaño + raza', () => {
    expect(tituloMascota(mascota({ nombre: '', raza: 'Labrador' }))).toBe('Perro mediano labrador');
  });

  it('sin raza no deja huecos ni cuelga el separador', () => {
    expect(tituloMascota(mascota({ nombre: '', raza: null }))).toBe('Perro mediano');
    expect(tituloMascota(mascota({ nombre: '   ', especie: 'gato', tamano: 'pequeño' }))).toBe(
      'Gato pequeño',
    );
  });

  it('la raza "Otra" no aporta señas y no se incluye', () => {
    expect(tituloMascota(mascota({ nombre: '', raza: 'Otra' }))).toBe('Perro mediano');
  });
});

// ── Copy de las solicitudes de adopción (AD-05) ──────────────────────────────
// Las dos listas van escritas a mano y tipadas contra su `Literal`: es lo que
// convierte estos casos en un anti-drift de verdad. Si mañana el backend suma un
// estado, `tsc` obliga a añadirlo al `Record` (o no compila) y estos casos se
// ponen rojos hasta que alguien decida su copy y su color — en vez de que la
// pantalla pinte `undefined` en un badge.
const ESTADOS: EstadoSolicitud[] = [
  'solicitado',
  'en_revision',
  'visita_agendada',
  'adoptado',
  'cerrado',
];

const ACCIONES: AccionSolicitud[] = ['agendar-visita', 'pedir-informacion', 'aprobar', 'descartar'];

describe('ETIQUETA_ESTADO_SOLICITUD', () => {
  it('los cinco estados tienen texto y color, ninguno vacío', () => {
    for (const estado of ESTADOS) {
      const badge = ETIQUETA_ESTADO_SOLICITUD[estado];
      expect(badge.texto.trim()).not.toBe('');
      expect(badge.color.trim()).not.toBe('');
    }
  });

  it('sus claves son exactamente los cinco estados persistidos', () => {
    expect(Object.keys(ETIQUETA_ESTADO_SOLICITUD).sort()).toEqual([...ESTADOS].sort());
  });

  it('avanzar es forest, esperar es ochre y cerrar es neutro', () => {
    expect(ETIQUETA_ESTADO_SOLICITUD.solicitado.color).toContain('ochre');
    expect(ETIQUETA_ESTADO_SOLICITUD.en_revision.color).toContain('ochre');
    expect(ETIQUETA_ESTADO_SOLICITUD.visita_agendada.color).toContain('forest');
    expect(ETIQUETA_ESTADO_SOLICITUD.adoptado.color).toContain('forest');
    expect(ETIQUETA_ESTADO_SOLICITUD.cerrado.color).toContain('muted');
  });

  // `danger` es el rojo de emergencia y está reservado en toda la app a
  // "perdido". Una solicitud cerrada no es una mala noticia del mismo orden que
  // una mascota perdida, y teñirla de rojo rompería esa señal en la única
  // pantalla donde los dos dominios pueden convivir.
  it('ningún estado usa danger: el rojo está reservado a "perdido"', () => {
    for (const estado of ESTADOS) {
      expect(ETIQUETA_ESTADO_SOLICITUD[estado].color).not.toContain('danger');
    }
  });
});

describe('ETIQUETA_ACCION_SOLICITUD', () => {
  it('las cuatro acciones tienen el copy exacto de los botones', () => {
    expect(ETIQUETA_ACCION_SOLICITUD['agendar-visita']).toBe('Agendar visita');
    expect(ETIQUETA_ACCION_SOLICITUD['pedir-informacion']).toBe('Pedir más información');
    expect(ETIQUETA_ACCION_SOLICITUD.aprobar).toBe('Confirmar adopción');
    expect(ETIQUETA_ACCION_SOLICITUD.descartar).toBe('Descartar solicitud');
  });

  // Anti-drift: las acciones son los últimos segmentos de
  // `POST /api/solicitudes/{id}/{accion}` y llegan del backend dentro de
  // `acciones_disponibles`. Una que no tenga etiqueta pintaría un botón vacío
  // que sí funciona al pulsarlo.
  it('sus claves son exactamente las cuatro acciones del backend', () => {
    expect(Object.keys(ETIQUETA_ACCION_SOLICITUD).sort()).toEqual([...ACCIONES].sort());
  });

  it('ninguna etiqueta nombra un estado ni promete que la acción ya ocurrió', () => {
    // "Aprobar" lleva a `adoptado` y "Descartar" a `cerrado`: las acciones NO
    // son estados (`aprobado` no existe como estado, y ese es el error que el
    // backend tiene explícitamente prohibido).
    for (const accion of ACCIONES) {
      expect(ETIQUETA_ACCION_SOLICITUD[accion]).not.toContain('aprobado');
      expect(ETIQUETA_ACCION_SOLICITUD[accion].trim()).not.toBe('');
    }
  });
});

describe('contarFiltrosActivos', () => {
  it('sin nada puesto devuelve cero', () => {
    expect(contarFiltrosActivos(FILTROS_ADOPCION_DEFAULT)).toBe(0);
  });

  it('cuenta cada valor elegido, no cada grupo tocado', () => {
    // "Filtros · 3" tiene que significar tres cosas elegidas: es lo que la
    // persona recuerda haber tocado, no cuántas familias de chips usó.
    expect(contarFiltrosActivos({ ...FILTROS_ADOPCION_DEFAULT, especie: ['perro', 'gato'] })).toBe(
      2,
    );
    expect(
      contarFiltrosActivos({
        ...FILTROS_ADOPCION_DEFAULT,
        especie: ['perro', 'gato'],
        tamano: ['pequeño'],
      }),
    ).toBe(3);
  });

  // ⚠️ El bug que motivó extraer esta función (AD-08 paso 7): el `hayFiltros`
  // del catálogo miraba especie, tamaño, energía y zona — y **se saltaba la
  // edad**. Con solo un tramo de edad puesto y cero resultados, la pantalla
  // decía "Todavía no hay mascotas publicadas": le contaba a la persona que el
  // catálogo estaba vacío cuando lo que pasaba es que su filtro no casaba.
  it('cuenta el tramo de edad (el grupo que el catálogo se saltaba)', () => {
    expect(contarFiltrosActivos({ ...FILTROS_ADOPCION_DEFAULT, edad: ['cachorro'] })).toBe(1);
  });

  it('la zona cuenta como uno, y "todas las zonas" no cuenta', () => {
    expect(contarFiltrosActivos({ ...FILTROS_ADOPCION_DEFAULT, zona: 'Cali' })).toBe(1);
    expect(contarFiltrosActivos({ ...FILTROS_ADOPCION_DEFAULT, zona: '' })).toBe(0);
  });

  // Anti-drift: si `FiltrosMascotas` gana un grupo y nadie lo suma aquí, el
  // panel plegado escondería un filtro activo sin decirlo — que es justo lo que
  // esta función existe para impedir. Un filtro por grupo, todos a la vez.
  it('con un filtro en cada grupo cuenta los cinco', () => {
    expect(
      contarFiltrosActivos({
        especie: ['perro'],
        tamano: ['mediano'],
        energia: ['baja'],
        edad: ['senior'],
        zona: 'Armenia',
      }),
    ).toBe(5);
  });
});
