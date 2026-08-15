import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';

// Node 22.4+ expone un `localStorage` nativo (Web Storage API, ya sin flag en Node 25)
// que, sin `--localstorage-file`, es un objeto vacío SIN métodos. El entorno jsdom de
// Vitest no pisa los globals que Node ya define, así que ese objeto roto le gana al
// Storage real de jsdom y toda llamada a getItem/setItem/clear revienta (los 147 tests
// de web fallaban con "localStorage.getItem is not a function" en Node 25.9).
// Se restaura un Storage en memoria SOLO si el global está roto: en Node 24, en CI y en
// cualquier entorno sano esto es un no-op y sigue mandando jsdom.
if (typeof globalThis.localStorage?.getItem !== 'function') {
  const almacen = new Map<string, string>();
  const storage: Storage = {
    get length() {
      return almacen.size;
    },
    key: (indice) => [...almacen.keys()][indice] ?? null,
    getItem: (clave) => almacen.get(clave) ?? null,
    setItem: (clave, valor) => void almacen.set(clave, String(valor)),
    removeItem: (clave) => void almacen.delete(clave),
    clear: () => almacen.clear(),
  };
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true,
    writable: true,
    value: storage,
  });
}

// localStorage es compartido dentro de un mismo archivo de test (jsdom no lo resetea
// solo); se limpia tras cada test para que ningún test que use lib/session.ts (o algo
// que lo use, como el gate de rutas de la feature 08) deje estado para el siguiente.
afterEach(() => {
  localStorage.clear();
});
