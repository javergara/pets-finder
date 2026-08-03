import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';

// localStorage es compartido dentro de un mismo archivo de test (jsdom no lo resetea
// solo); se limpia tras cada test para que ningún test que use lib/session.ts (o algo
// que lo use, como el gate de rutas de la feature 08) deje estado para el siguiente.
afterEach(() => {
  localStorage.clear();
});
