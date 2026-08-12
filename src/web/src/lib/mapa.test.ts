import { describe, expect, it } from 'vitest';
import { COLOMBIA, NOMBRES_ZONAS, ZONAS, cajaDeZona } from './ciudades';
import { coordsDesdeFraccion, posicionEnMapa } from './mapa';

describe('posicionEnMapa', () => {
  it('el centro declarado de cada zona cae dentro del lienzo (0-100%)', () => {
    for (const nombre of NOMBRES_ZONAS) {
      const caja = ZONAS[nombre];
      const { left, top } = posicionEnMapa(caja.centroLat, caja.centroLng, nombre);
      expect(parseFloat(left)).toBeGreaterThanOrEqual(0);
      expect(parseFloat(left)).toBeLessThanOrEqual(100);
      expect(parseFloat(top)).toBeGreaterThanOrEqual(0);
      expect(parseFloat(top)).toBeLessThanOrEqual(100);
    }
  });

  it('la esquina noroeste (lat máxima, lng mínima) cae en la esquina superior izquierda', () => {
    const caja = ZONAS.Armenia;
    expect(posicionEnMapa(caja.latMax, caja.lngMin, 'Armenia')).toEqual({
      left: '0%',
      top: '0%',
    });
  });

  it('la esquina opuesta (lat mínima, lng máxima) cae en la esquina inferior derecha', () => {
    const caja = ZONAS.Bogotá;
    expect(posicionEnMapa(caja.latMin, caja.lngMax, 'Bogotá')).toEqual({
      left: '100%',
      top: '100%',
    });
  });

  it('una zona desconocida ("Otro", "Colombia") usa el lienzo nacional', () => {
    expect(cajaDeZona('Otro')).toEqual(COLOMBIA);
    expect(posicionEnMapa(COLOMBIA.latMax, COLOMBIA.lngMin, 'Colombia')).toEqual({
      left: '0%',
      top: '0%',
    });
  });
});

describe('coordsDesdeFraccion (inversa de posicionEnMapa)', () => {
  it('el centro del lienzo (0.5, 0.5) devuelve el punto medio del bounding box', () => {
    const { lat, lng } = coordsDesdeFraccion(0.5, 0.5, 'Bogotá');
    expect(lat).toBeCloseTo((ZONAS.Bogotá.latMin + ZONAS.Bogotá.latMax) / 2, 3);
    expect(lng).toBeCloseTo((ZONAS.Bogotá.lngMin + ZONAS.Bogotá.lngMax) / 2, 3);
  });

  it('roundtrip fracción→coords→posición para todas las zonas y el lienzo nacional', () => {
    const fracciones: Array<[number, number]> = [
      [0, 0],
      [0.25, 0.75],
      [0.5, 0.5],
      [1, 1],
    ];
    for (const zona of [...NOMBRES_ZONAS, 'Otro']) {
      for (const [fx, fy] of fracciones) {
        const { lat, lng } = coordsDesdeFraccion(fx, fy, zona);
        const { left, top } = posicionEnMapa(lat, lng, zona);
        expect(parseFloat(left)).toBeCloseTo(fx * 100, 1);
        expect(parseFloat(top)).toBeCloseTo(fy * 100, 1);
      }
    }
  });
});
