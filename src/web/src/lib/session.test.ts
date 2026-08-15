import { afterEach, describe, expect, it } from 'vitest';
import { DEMO_USER_ID } from './constants';
import { esUsuarioActivo, getActiveUserId, hasActiveUser, setActiveUserId } from './session';

afterEach(() => {
  localStorage.clear();
});

describe('session', () => {
  // Guarda del entorno de tests: en Node 22.4+ el `localStorage` nativo (sin
  // --localstorage-file) es un objeto sin métodos y le gana al Storage de jsdom.
  // src/test/setup.ts lo repara; si esa reparación se cae, este test lo dice en una
  // línea en vez de dejar 147 tests rojos con un TypeError críptico.
  it('el entorno de tests expone un localStorage utilizable', () => {
    expect(typeof localStorage.getItem).toBe('function');
    expect(typeof localStorage.setItem).toBe('function');
    expect(typeof localStorage.clear).toBe('function');
  });

  it('sin nada en localStorage, devuelve DEMO_USER_ID como fallback', () => {
    expect(getActiveUserId()).toBe(DEMO_USER_ID);
  });

  it('tras setActiveUserId, getActiveUserId devuelve el id guardado', () => {
    setActiveUserId(7);

    expect(getActiveUserId()).toBe(7);
  });

  it('hasActiveUser distingue "nunca se registró" del fallback DEMO_USER_ID', () => {
    expect(hasActiveUser()).toBe(false);

    setActiveUserId(DEMO_USER_ID);

    expect(hasActiveUser()).toBe(true);
  });
});

// Fix 2026-08-15 (bug de autoría sin cuenta): comparar a mano contra
// getActiveUserId() convertía a cualquier visitante anónimo en el usuario
// DEMO_USER_ID, que es una persona real en producción. Este es el caso que
// ninguna pantalla debe volver a resolver por su cuenta.
describe('esUsuarioActivo', () => {
  it('sin cuenta es false, incluso para el DEMO_USER_ID al que cae getActiveUserId', () => {
    expect(getActiveUserId()).toBe(DEMO_USER_ID);

    expect(esUsuarioActivo(DEMO_USER_ID)).toBe(false);
  });

  it('con cuenta, es true solo para su propio id', () => {
    setActiveUserId(7);

    expect(esUsuarioActivo(7)).toBe(true);
  });

  it('con cuenta, el id de otra persona es false', () => {
    setActiveUserId(7);

    expect(esUsuarioActivo(2)).toBe(false);
    // null/undefined llegan de recursos sin dueño (una organización eliminada);
    // nadie es su autor.
    expect(esUsuarioActivo(null)).toBe(false);
    expect(esUsuarioActivo(undefined)).toBe(false);
  });
});
