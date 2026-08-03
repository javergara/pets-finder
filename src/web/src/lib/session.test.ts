import { afterEach, describe, expect, it } from 'vitest';
import { DEMO_USER_ID } from './constants';
import { getActiveUserId, setActiveUserId } from './session';

afterEach(() => {
  localStorage.clear();
});

describe('session', () => {
  it('sin nada en localStorage, devuelve DEMO_USER_ID como fallback', () => {
    expect(getActiveUserId()).toBe(DEMO_USER_ID);
  });

  it('tras setActiveUserId, getActiveUserId devuelve el id guardado', () => {
    setActiveUserId(7);

    expect(getActiveUserId()).toBe(7);
  });
});
