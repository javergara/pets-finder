import { useEffect, useRef, useState } from 'react';
import { chatSocketUrl, obtenerThread } from '../api/client';
import type { Message } from '../api/types';

interface ChatHiloProps {
  matchId: number;
  rol: 'adoptante' | 'refugio';
  participantId: number;
  mostrarRespuestasRapidas: boolean;
}

// Simplificación consciente para el alcance de esta feature: los chips envían un texto
// literal fijo, no hay ninguna detección de intención de "el refugio está proponiendo
// una cita" en el texto entrante -- eso requeriría un clasificador que no se justifica
// para un MVP local. El diseño (design/screens/mensajes.md) los describe como "siempre
// visibles" del lado adoptante, así que se muestran de forma incondicional.
const RESPUESTAS_RAPIDAS = ['Sí, agendar', 'Proponer otra hora'];

export function ChatHilo({ matchId, rol, participantId, mostrarRespuestasRapidas }: ChatHiloProps) {
  const [mensajes, setMensajes] = useState<Message[] | null>(null);
  const [texto, setTexto] = useState('');
  const [conexionPerdida, setConexionPerdida] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Historial inicial vía REST (idempotente: crea el hilo + mensaje de sistema si
  // todavía no existía).
  useEffect(() => {
    let activo = true;
    setMensajes(null);
    obtenerThread(matchId).then((data) => {
      if (activo) setMensajes(data.mensajes);
    });
    return () => {
      activo = false;
    };
  }, [matchId]);

  // Conexión WS aparte del historial: solo mensajes nuevos desde que se conecta
  // (routers/chat.py no reenvía historial por el socket). Guardamos la instancia en un
  // ref para poder cerrarla en el cleanup del efecto y no dejar sockets huérfanos
  // escuchando en segundo plano en cada re-render/desmontaje.
  useEffect(() => {
    const ws = new WebSocket(chatSocketUrl(matchId, rol, participantId));
    wsRef.current = ws;
    setConexionPerdida(false);

    ws.onmessage = (event) => {
      const mensaje = JSON.parse(event.data as string) as Message;
      setMensajes((prev) => (prev ? [...prev, mensaje] : [mensaje]));
    };
    ws.onclose = () => {
      setConexionPerdida(true);
    };

    return () => {
      // Evita que el cierre intencional al desmontar/re-crear el efecto dispare
      // "se perdió la conexión" -- ese aviso es solo para un cierre inesperado.
      ws.onclose = null;
      ws.close();
      wsRef.current = null;
    };
  }, [matchId, rol, participantId]);

  function enviarTexto(valor: string) {
    const contenido = valor.trim();
    if (!contenido || !wsRef.current) return;
    wsRef.current.send(JSON.stringify({ texto: contenido }));
  }

  function handleEnviar(e: React.FormEvent) {
    e.preventDefault();
    enviarTexto(texto);
    setTexto('');
  }

  if (mensajes === null) {
    return (
      <div className="mx-auto flex max-w-2xl flex-col gap-3 p-6">
        <div className="h-10 w-2/3 animate-pulse rounded-xl bg-surface-alt" />
        <div className="h-16 w-1/2 animate-pulse rounded-2xl bg-surface-alt" />
        <div className="ml-auto h-16 w-1/2 animate-pulse rounded-2xl bg-surface-alt" />
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-3 p-6">
      <div className="flex flex-col gap-2">
        {mensajes.map((mensaje) => {
          if (mensaje.autor_tipo === 'sistema') {
            return (
              <p
                key={mensaje.id}
                className="rounded-xl bg-surface-alt p-3 text-center text-sm text-muted"
              >
                {mensaje.texto}
              </p>
            );
          }

          const esPropio = mensaje.autor_tipo === rol;
          return (
            <div key={mensaje.id} className={`flex ${esPropio ? 'justify-end' : 'justify-start'}`}>
              <p
                className={`max-w-[62%] px-4 py-2 text-sm ${
                  esPropio
                    ? 'rounded-[14px_14px_4px_14px] bg-forest text-bg'
                    : 'rounded-[14px_14px_14px_4px] border border-line bg-surface text-ink'
                }`}
              >
                {mensaje.texto}
              </p>
            </div>
          );
        })}
      </div>

      {conexionPerdida && (
        <p className="text-xs text-danger">
          Se perdió la conexión del chat. Recarga la página para reconectar.
        </p>
      )}

      {mostrarRespuestasRapidas && (
        <div className="flex flex-wrap gap-2">
          {RESPUESTAS_RAPIDAS.map((respuesta) => (
            <button
              key={respuesta}
              type="button"
              onClick={() => enviarTexto(respuesta)}
              className="rounded-full border border-forest-tint-line bg-forest-tint px-3 py-1.5 text-sm text-forest"
            >
              {respuesta}
            </button>
          ))}
        </div>
      )}

      <form onSubmit={handleEnviar} className="flex gap-2 border-t border-line pt-3">
        <input
          type="text"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Escribe un mensaje..."
          className="flex-1 rounded-full border border-line bg-surface px-4 py-2 text-ink"
        />
        <button
          type="submit"
          disabled={texto.trim().length === 0}
          className="rounded-full bg-forest px-4 py-2 font-medium text-bg disabled:opacity-40"
        >
          Enviar
        </button>
      </form>
    </div>
  );
}
