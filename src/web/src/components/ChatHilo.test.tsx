import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as client from '../api/client';
import type { ThreadConMensajes } from '../api/types';
import { MockWebSocket } from '../test/mockWebSocket';
import { ChatHilo } from './ChatHilo';

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
      texto: 'Se abrió esta conversación porque hiciste match con Canela de Refugio Huellas.',
      creado_en: '2026-01-01T00:00:00Z',
    },
    {
      id: 2,
      autor_tipo: 'refugio',
      texto: 'Hola, gracias por tu interés en Canela.',
      creado_en: '2026-01-01T00:01:00Z',
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

describe('ChatHilo', () => {
  it('carga el historial: el aviso de sistema se renderiza primero y distinto a las burbujas de conversación', async () => {
    vi.mocked(client.obtenerThread).mockResolvedValue(THREAD_BASE);

    render(
      <ChatHilo matchId={1} rol="adoptante" participantId={1} mostrarRespuestasRapidas={false} />,
    );

    const aviso = await screen.findByText(/se abrió esta conversación/i);
    const burbuja = screen.getByText('Hola, gracias por tu interés en Canela.');

    // El aviso de sistema no lleva las clases de burbuja de conversación (usa
    // `bg-surface-alt`, no `bg-forest` ni `bg-surface` de las burbujas).
    expect(aviso.className).not.toContain('bg-forest');
    expect(aviso.className).toContain('bg-surface-alt');
    expect(burbuja.className).toContain('bg-surface');
    expect(burbuja.className).not.toContain('bg-surface-alt');

    // Orden: el aviso aparece antes que la burbuja en el documento.
    expect(aviso.compareDocumentPosition(burbuja) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('marca las burbujas propias vs. ajenas según el rol de la conexión', async () => {
    vi.mocked(client.obtenerThread).mockResolvedValue(THREAD_BASE);

    render(
      <ChatHilo matchId={1} rol="refugio" participantId={1} mostrarRespuestasRapidas={false} />,
    );

    const burbujaPropia = await screen.findByText('Hola, gracias por tu interés en Canela.');
    expect(burbujaPropia.className).toContain('bg-forest');
    expect(burbujaPropia.className).toContain('rounded-[14px_14px_4px_14px]');
  });

  it('agrega al historial un mensaje entrante recibido por el WebSocket', async () => {
    vi.mocked(client.obtenerThread).mockResolvedValue(THREAD_BASE);

    render(
      <ChatHilo matchId={1} rol="adoptante" participantId={1} mostrarRespuestasRapidas={false} />,
    );

    await screen.findByText('Hola, gracias por tu interés en Canela.');

    const socket = MockWebSocket.instances[0];
    socket.onmessage?.({
      data: JSON.stringify({
        id: 3,
        autor_tipo: 'adoptante',
        texto: 'Perfecto, ¿cuándo puedo visitarla?',
        creado_en: '2026-01-01T00:02:00Z',
      }),
    });

    expect(await screen.findByText('Perfecto, ¿cuándo puedo visitarla?')).toBeInTheDocument();
    // No reemplaza el historial previo, solo hace append.
    expect(screen.getByText('Hola, gracias por tu interés en Canela.')).toBeInTheDocument();
  });

  it('el compositor envía el texto escrito por el WebSocket, no por REST', async () => {
    vi.mocked(client.obtenerThread).mockResolvedValue(THREAD_BASE);

    render(
      <ChatHilo matchId={1} rol="adoptante" participantId={1} mostrarRespuestasRapidas={false} />,
    );

    await screen.findByText('Hola, gracias por tu interés en Canela.');

    const socket = MockWebSocket.instances[0];
    const input = screen.getByPlaceholderText('Escribe un mensaje...');
    fireEvent.change(input, { target: { value: 'Hola, sí me interesa mucho' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar' }));

    expect(socket.send).toHaveBeenCalledWith(
      JSON.stringify({ texto: 'Hola, sí me interesa mucho' }),
    );
  });

  it('cierra el socket en el cleanup del efecto (no deja conexiones huérfanas)', async () => {
    vi.mocked(client.obtenerThread).mockResolvedValue(THREAD_BASE);

    const { unmount } = render(
      <ChatHilo matchId={1} rol="adoptante" participantId={1} mostrarRespuestasRapidas={false} />,
    );

    await screen.findByText('Hola, gracias por tu interés en Canela.');
    const socket = MockWebSocket.instances[0];

    unmount();

    expect(socket.close).toHaveBeenCalledTimes(1);
  });
});
