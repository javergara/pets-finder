import { describe, expect, it } from 'vitest';
import type { Mascota } from '../api/types';
import { categoriaEdad, edadLegible, tituloMascota } from './adopcion';

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
