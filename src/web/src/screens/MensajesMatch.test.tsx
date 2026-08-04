import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { ThreadConMensajes } from '../api/types';
import { MockWebSocket } from '../test/mockWebSocket';
import { MensajesMatch } from './MensajesMatch';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof client>('../api/client');
  return { ...actual, obtenerThread: vi.fn() };
});

const THREAD_BASE: ThreadConMensajes = {
  thread: {
    id: 1,
    match_id: 1,
    creado_en: '2026-01-01T00:00:00Z',
    ultimo_mensaje_en: '2026-01-01T00:00:00Z',
  },
  mensajes: [
    {
      id: 1,
      autor_tipo: 'sistema',
      texto: 'Se abrió esta conversación porque hiciste match con Canela.',
      creado_en: '2026-01-01T00:00:00Z',
    },
  ],
};

beforeEach(() => {
  MockWebSocket.reset();
  vi.stubGlobal('WebSocket', MockWebSocket);
});

afterEach(() => {
  vi.resetAllMocks();
  vi.unstubAllGlobals();
});

function renderConRouter(matchId = '1') {
  return render(
    <MemoryRouter initialEntries={[`/matches/${matchId}/mensajes`]}>
      <Routes>
        <Route path="/matches/:matchId/mensajes" element={<MensajesMatch />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('MensajesMatch', () => {
  it('muestra los dos chips de respuesta rápida del lado adoptante', async () => {
    vi.mocked(client.obtenerThread).mockResolvedValue(THREAD_BASE);

    renderConRouter();

    expect(await screen.findByRole('button', { name: 'Sí, agendar' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Proponer otra hora' })).toBeInTheDocument();
  });

  it('al pulsar cada chip, envía el texto literal exacto por el WebSocket', async () => {
    vi.mocked(client.obtenerThread).mockResolvedValue(THREAD_BASE);

    renderConRouter();

    await screen.findByRole('button', { name: 'Sí, agendar' });
    const socket = MockWebSocket.instances[0];

    fireEvent.click(screen.getByRole('button', { name: 'Sí, agendar' }));
    expect(socket.send).toHaveBeenCalledWith(JSON.stringify({ texto: 'Sí, agendar' }));

    fireEvent.click(screen.getByRole('button', { name: 'Proponer otra hora' }));
    expect(socket.send).toHaveBeenCalledWith(JSON.stringify({ texto: 'Proponer otra hora' }));
  });
});
