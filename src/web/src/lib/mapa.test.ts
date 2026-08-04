import { describe, expect, it } from 'vitest';
import { posicionEnMapa } from './mapa';

describe('posicionEnMapa', () => {
  it('el punto medio del bounding box cae en el centro del lienzo', () => {
    expect(posicionEnMapa(4.675, -74.1)).toEqual({ left: '50%', top: '50%' });
  });

  it('la esquina noroeste (lat máxima, lng mínima) cae en la esquina superior izquierda', () => {
    expect(posicionEnMapa(4.8, -74.2)).toEqual({ left: '0%', top: '0%' });
  });

  it('la esquina opuesta (lat mínima, lng máxima) cae en la esquina inferior derecha', () => {
    expect(posicionEnMapa(4.55, -74.0)).toEqual({ left: '100%', top: '100%' });
  });
});
