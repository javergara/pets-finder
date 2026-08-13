import { describe, expect, it } from 'vitest';
import { tituloReporte } from './titulo';

function reporte(overrides = {}) {
  return {
    nombre_mascota: null,
    especie: 'perro' as const,
    tamano: null,
    color: null,
    ...overrides,
  };
}

describe('tituloReporte', () => {
  it('con nombre, el nombre manda', () => {
    expect(tituloReporte(reporte({ nombre_mascota: 'Rocky', color: 'Negro' }))).toBe('Rocky');
  });

  it('sin nombre compone especie + tamaño + color en minúscula', () => {
    expect(tituloReporte(reporte({ tamano: 'mediano', color: 'Café' }))).toBe('Perro mediano café');
  });

  it('omite los atributos ausentes sin dejar huecos', () => {
    expect(tituloReporte(reporte())).toBe('Perro');
    expect(tituloReporte(reporte({ especie: 'gato', color: 'Atigrado' }))).toBe('Gato atigrado');
    expect(tituloReporte(reporte({ tamano: 'grande' }))).toBe('Perro grande');
  });

  it('el color "Otro" no aporta señas y no se incluye', () => {
    expect(tituloReporte(reporte({ tamano: 'pequeño', color: 'Otro' }))).toBe('Perro pequeño');
  });
});
