import { vi } from 'vitest';

// Mock mínimo de la clase WebSocket global para tests de componentes que abren un
// socket (ChatHilo y las pantallas que lo envuelven). Se usa vía
// `vi.stubGlobal('WebSocket', MockWebSocket)`. Los tests disparan `onopen`/`onmessage`/
// `onclose` manualmente (son propiedades públicas, no eventos reales de jsdom) y
// verifican `send`/`close` como espías (`vi.fn()`).
export class MockWebSocket {
  static instances: MockWebSocket[] = [];

  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  addEventListener = vi.fn();
  send = vi.fn();
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  static reset() {
    MockWebSocket.instances = [];
  }
}
