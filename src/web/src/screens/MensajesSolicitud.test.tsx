import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { ThreadConMensajes } from '../api/types';
import { MockWebSocket } from '../test/mockWebSocket';
import { MensajesSolicitud } from './MensajesSolicitud';

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
    <MemoryRouter initialEntries={[`/refugio/solicitudes/${matchId}/mensajes`]}>
      <Routes>
        <Route path="/refugio/solicitudes/:matchId/mensajes" element={<MensajesSolicitud />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('MensajesSolicitud', () => {
  it('no muestra los chips de respuesta rápida del lado refugio', async () => {
    vi.mocked(client.obtenerThread).mockResolvedValue(THREAD_BASE);

    renderConRouter();

    await screen.findByText('Se abrió esta conversación porque hiciste match con Canela.');

    expect(screen.queryByRole('button', { name: 'Sí, agendar' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Proponer otra hora' })).not.toBeInTheDocument();
  });
});
