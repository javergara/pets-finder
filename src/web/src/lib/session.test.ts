import { afterEach, describe, expect, it } from 'vitest';
import { DEMO_USER_ID } from './constants';
import { getActiveUserId, hasActiveUser, setActiveUserId } from './session';

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
