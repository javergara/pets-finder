import { describe, expect, it } from 'vitest';
import { tiempoRelativo } from './tiempo';

// "Ahora" fijo para que los casos sean deterministas.
const AHORA = new Date('2026-08-12T15:00:00Z');

describe('tiempoRelativo', () => {
  it('cubre los rangos de minutos, horas, días y semanas', () => {
    expect(tiempoRelativo('2026-08-12T14:59:30', AHORA)).toBe('hace un momento');
    expect(tiempoRelativo('2026-08-12T14:45:00', AHORA)).toBe('hace 15 min');
    expect(tiempoRelativo('2026-08-12T14:00:00', AHORA)).toBe('hace 1 hora');
    expect(tiempoRelativo('2026-08-12T09:00:00', AHORA)).toBe('hace 6 horas');
    expect(tiempoRelativo('2026-08-11T10:00:00', AHORA)).toBe('ayer');
    expect(tiempoRelativo('2026-08-09T15:00:00', AHORA)).toBe('hace 3 días');
    expect(tiempoRelativo('2026-08-04T15:00:00', AHORA)).toBe('hace 1 semana');
    expect(tiempoRelativo('2026-07-20T15:00:00', AHORA)).toBe('hace 3 semanas');
  });

  it('trata los timestamps sin zona del backend como UTC', () => {
    // Con y sin sufijo Z deben dar lo mismo.
    expect(tiempoRelativo('2026-08-12T14:00:00', AHORA)).toBe(
      tiempoRelativo('2026-08-12T14:00:00Z', AHORA),
    );
  });
});
